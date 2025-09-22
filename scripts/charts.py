#!/usr/bin/env python3
import sys
import re
import matplotlib.pyplot as plt
from datetime import datetime

def parse_ab_summary(file_path):
    metrics = {}
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [ln.rstrip('\n') for ln in f]

    # Join for some regexes but also keep lines for line-based parsing
    content = '\n'.join(lines)

    # Tolerant extraction helpers
    def find_first_number_on_line_containing(token):
        for ln in lines:
            if token.lower() in ln.lower():
                m = re.search(r'(-?\d+(\.\d+)?)', ln)
                if m:
                    # return int if integer-like, else float
                    val = m.group(1)
                    return int(val) if re.match(r'^-?\d+$', val) else float(val)
        return None

    def find_number_by_regex(pattern, cast=float):
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            val = m.group(1)
            return cast(val)
        return None

    # Robust patterns (try several forms)
    metrics['Total Requests'] = find_number_by_regex(r'Total Requests:\s*(\d+)', int) or find_first_number_on_line_containing('Complete requests') or 0
    metrics['Requests per Second'] = find_number_by_regex(r'Requests per Second:\s*([\d.]+)', float) or find_first_number_on_line_containing('Requests per second') or 0.0
    metrics['Average Latency (Total)'] = find_number_by_regex(r'Average Latency $Total$:\s*([\d.]+)', float) or find_number_by_regex(r'Time per request:\s*([\d.]+)', float) or 0.0
    metrics['90% of requests served in'] = find_number_by_regex(r'90%.*?served in[:\s]*([\d.]+)', float) or find_first_number_on_line_containing('90%') or 0.0

    # Connection times: prefer reading the second numeric token on the matching line (min mean [max])
    def mean_from_line(token):
        for ln in lines:
            if token.lower() in ln.lower():
                nums = re.findall(r'(-?\d+(\.\d+)?)', ln)
                nums = [n[0] for n in nums]
                if len(nums) >= 2:
                    # second numeric token is mean
                    v = nums[1]
                    return float(v) if '.' in v else int(v)
                elif nums:
                    return float(nums[0]) if '.' in nums[0] else int(nums[0])
        return 0

    metrics['Mean Connection Time'] = mean_from_line('Connect') or 0
    metrics['Mean Processing Time'] = mean_from_line('Processing') or 0
    metrics['Mean Waiting Time'] = mean_from_line('Waiting') or 0

    # Failed requests: find the line containing "Failed" and extract the first integer on it.
    failed_val = find_first_number_on_line_containing('Failed')
    if failed_val is None:
        # try alternative tokens
        failed_val = find_first_number_on_line_containing('Non-2xx') or find_first_number_on_line_containing('Errors') or 0
    metrics['Failed Requests'] = int(failed_val)

    # Transfer rate
    tr = find_number_by_regex(r'Transfer rate:\s*([\d.]+)', float)
    metrics['Transfer Rate'] = tr or find_first_number_on_line_containing('Transfer rate') or 0.0

    # Ensure numeric types
    metrics['Total Requests'] = int(metrics['Total Requests'])
    metrics['Failed Requests'] = int(metrics['Failed Requests'])
    for k in ['Requests per Second', 'Average Latency (Total)', 'Mean Connection Time', 'Mean Processing Time', 'Mean Waiting Time', '90% of requests served in', 'Transfer Rate']:
        metrics[k] = float(metrics.get(k, 0.0))

    # Debug lines that mention failed/errors
    metrics['_debug_failed_lines'] = [ln for ln in lines if re.search(r'failed|non-2xx|errors', ln, re.IGNORECASE)]

    return metrics

def nicer_colors():
    return {
        'connect': '#4E88C3',
        'waiting': '#F17E7E',
        'processing': '#8BC48A',
        'success': '#6CC070',
        'failed': '#F15B5B',
        'bg': '#FFFFFF'
    }

def create_and_save_charts(metrics, input_filename):
    colors = nicer_colors()
    connect = metrics.get('Mean Connection Time', 0.0)
    waiting = metrics.get('Mean Waiting Time', 0.0)
    processing = metrics.get('Mean Processing Time', 0.0)
    total_latency_sum = connect + waiting + processing
    total_latency_display = metrics.get('Average Latency (Total)', total_latency_sum)

    fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(14, 7), dpi=120)
    fig.patch.set_facecolor(colors['bg'])

    components = [connect, waiting, processing]
    comp_labels = ['Connect', 'Waiting', 'Processing']
    comp_colors = [colors['connect'], colors['waiting'], colors['processing']]

    if total_latency_sum == 0 and total_latency_display > 0:
        components = [total_latency_display]
        comp_labels = ['Total Latency']
        comp_colors = ['#7D7D7D']

    left = 0
    for val, c in zip(components, comp_colors):
        ax_bar.barh(0, val, left=left, color=c, height=0.6)
        left += val

    ax_bar.set_title('Mean Latency Breakdown (ms)', fontsize=14, weight='bold')
    ax_bar.set_xlim(0, max(total_latency_display, total_latency_sum, 1) * 1.15)
    ax_bar.set_yticks([])
    ax_bar.grid(axis='x', linestyle='--', alpha=0.4)

    base = 0
    for val, label, col in zip(components, comp_labels, comp_colors):
        if val <= 0:
            continue
        pct = (val / (total_latency_display if total_latency_display > 0 else 1)) * 100
        x = base + val / 2
        ax_bar.text(x, 0, f'{label}\n{val:.1f} ms\n{pct:.1f}%', ha='center', va='center', color='white', fontsize=10, weight='semibold')
        base += val

    ax_bar.annotate(f'Total (avg): {total_latency_display:.1f} ms', xy=(1.02, 0.5), xycoords='axes fraction', fontsize=12, weight='bold')

    total = metrics.get('Total Requests', 0)
    failed = metrics.get('Failed Requests', 0)
    successful = max(0, total - failed)

    ax_pie.set_title('Request Outcome', fontsize=14, weight='bold')
    if total == 0:
        ax_pie.text(0.5, 0.5, 'No requests', ha='center', va='center', fontsize=12)
        ax_pie.axis('off')
    else:
        sizes = [successful, failed]
        labels = [f'Successful\n{successful}', f'Failed\n{failed}']
        pie_colors = [colors['success'], colors['failed']]

        wedges, texts, autotexts = ax_pie.pie(
            sizes,
            labels=labels,
            colors=pie_colors,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 0 else '',
            startangle=90,
            pctdistance=0.75,
            textprops={'fontsize': 11, 'weight': 'semibold'}
        )

        centre_circle = plt.Circle((0,0),0.48,fc=colors['bg'])
        ax_pie.add_artist(centre_circle)
        ax_pie.axis('equal')

        fail_pct = (failed / total) * 100 if total > 0 else 0.0
        ax_pie.text(0, 0, f'{total}\nrequests\n{fail_pct:.1f}% failed', ha='center', va='center', fontsize=11, weight='bold')

        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_weight('bold')

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.suptitle(f'Apache Bench Results — {input_filename}  •  Generated: {now}', fontsize=16, weight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    out_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_name = f'ab_results_{out_ts}.png'
    plt.savefig(out_name, bbox_inches='tight', dpi=150)
    print(f'Chart saved as {out_name}')

    if metrics.get('_debug_failed_lines'):
        print('Debug lines containing failed/errors:')
        for ln in metrics['_debug_failed_lines']:
            print('  ' + ln)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 visualize_ab_results.py <summary.txt>')
        sys.exit(1)
    infile = sys.argv[1]
    try:
        data = parse_ab_summary(infile)
        print('Parsed metrics:')
        for k,v in data.items():
            if k != '_debug_failed_lines':
                print(f'  {k}: {v}')
        create_and_save_charts(data, infile)
    except FileNotFoundError:
        print(f"Error: The file '{infile}' was not found.")
    except Exception as e:
        print('Unexpected error:', e)

