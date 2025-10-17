import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    TimeScale,
    PointElement,
    LineElement,
    ChartOptions,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
ChartJS.defaults.color = 'rgba(70 70 70)'
import { NTPData } from '../utils/types.ts'
import { Measurement } from '../utils/types.ts'
import 'chartjs-adapter-date-fns';
import { ChartDataset } from 'chart.js';

type ChartInputData = {
    data: Map<string, NTPData[]> | null
    selectedMeasurement: Measurement
    selectedOption: string
    customRange?: { from: string; to: string }
    legendDisplay?: boolean
}

ChartJS.register(CategoryScale, LinearScale, TimeScale, PointElement, LineElement, Title, Tooltip, Legend)

/**
 * Remove points that are closer than `thresholdMs` to the previous *kept* point.
 * – `pts` must be time-sorted (you already have `sortedData` for that)
 * – Returns a new array; does NOT mutate the input.
 */
function thinByProximity<T extends { time: string | number | Date }>(
  pts: T[],
  thresholdMs: number
): T[] {
  if (pts.length === 0) return [];
  const out: T[] = [pts[0]];
  let last = new Date(pts[0].time).getTime();

  for (let i = 1; i < pts.length; i++) {
    const t = new Date(pts[i].time).getTime();
    if (t - last >= thresholdMs) {     // keep only if far enough apart
      out.push(pts[i]);
      last = t;
    }
  }
  return out;
}
/**
 *
 * @param count the number of servers on the graphs
 * @returns an array of strings representing the colors of the graphs
 */
function generateGradientColors(count: number): string[] {
    const colors: string[] = [];
    for (let i = 0; i < count; i++) {
        const ratio = i / Math.max(count - 1, 1); // Normalize between 0 and 1
        const red = Math.round(255 * ratio);
        const green = 0;
        const blue = Math.round(255 * (1 - ratio));
        colors.push(`rgb(${red}, ${green}, ${blue})`);
    }
    return colors;
}

function unitForSpan(spanMs: number): { unit: 'second'|'minute'|'hour'|'day'|'month'|'year', fmt: string } {
  const s = 1000, m = 60*s, h = 60*m, d = 24*h, y = 365*d;

  if (spanMs <= 2*h)          return { unit: 'minute', fmt: 'HH:mm' };       // up to ~2 h → show minutes
  if (spanMs <= 2*d)          return { unit: 'hour',   fmt: 'HH:mm' };       // up to ~2 days → hours
  if (spanMs <= 90*d)         return { unit: 'day',    fmt: 'dd MMM' };      // up to 3 months → days
  if (spanMs <= 2*y)          return { unit: 'month',  fmt: 'MMM yyyy' };    // up to 2 years → months
  return                        { unit: 'year',   fmt: 'yyyy' };             // above 2 years → years
}

export default function LineChart({data, selectedMeasurement, selectedOption, customRange, legendDisplay}: ChartInputData) {
  const measurementMap = {
      RTT: 'Round-trip time (ms)',
      offset: 'Offset (ms)'
  }
  if (data == null)
    return null


  const now = new Date()
  const graphColors: string[] = generateGradientColors(data.size)
  //
  // format X axis labels based on which time interval is selected
  //
  // start and end points, these can be modified for custom intervals
  let startingPoint = new Date(now)
  let endPoint = new Date(now)

  let customTimeUnit: 'second'|'minute'|'hour'|'day'|'month'|'year' | null = null;
  let customFmt = '';

  switch (selectedOption) {
    case "Last Hour":
      startingPoint.setHours(now.getHours() - 1)
      break
    case "Last Day":
      startingPoint.setDate(now.getDate() - 1)
      break
    case "Last Week":
      startingPoint.setDate(now.getDate() - 7)
      break
    case "Custom": {
      if (customRange?.from) startingPoint = new Date(customRange.from);
      if (customRange?.to)   endPoint     = new Date(customRange.to);

      // Ensure startingPoint and endPoint don't exceed current time
      if (startingPoint.getTime() > now.getTime()) {
        startingPoint = new Date(now);
      }
      if (endPoint.getTime() > now.getTime()) {
        endPoint = new Date(now);
      }

      const { unit, fmt } = unitForSpan(endPoint.getTime() - startingPoint.getTime());

      customTimeUnit = unit;
      customFmt      = fmt;
      break;
    }
    default:
      break;

  }

  /*SAMPLE_DENSITY represents the approximate maximum number of points that can be displayed on the graph */
  const SAMPLE_DENSITY = 100;  // data points reduction factor

  const axisMs = endPoint.getTime() - startingPoint.getTime();
  // const datasets: any[] = [];
  const datasets: ChartDataset<'line', { x: string; y: number }[]>[] = [];
  const thresholdMs =
        SAMPLE_DENSITY > 0 && axisMs > 0
          ? axisMs / SAMPLE_DENSITY
          : 0;
  //sort data chronologically for every server IP or name
  let clrIndex = 0 // used to iterate through the colors array
  for (const [server, series] of data.entries()) {
    const sortedSeries = [...series].sort((a, b) =>
      new Date(a.time).getTime() - new Date(b.time).getTime()
    );

    const thinned = thinByProximity(sortedSeries, thresholdMs);

    const points = thinned.map(d => ({
      x: new Date(d.time).toISOString(),
      y: d[selectedMeasurement]
    }));

    datasets.push({
      label: `${server}`,
      data: points,
      borderColor: graphColors[clrIndex++],
      backgroundColor: 'rgba(236, 240, 243, 0.3)',
      tension: 0,
      pointRadius: 2,
    });
  }

  const yValues: number[] = datasets.flatMap(ds => ds.data.map(p => p.y));
  let minY = 0, maxY = 1;
  if (yValues.length) {
    const minV = Math.min(...yValues);
    const maxV = Math.max(...yValues);
    const pad  = (maxV - minV || 1) * 0.1; // 10% padding above and below the min/max values
    minY = minV - pad;
    maxY = maxV + pad;
    if (selectedMeasurement === 'RTT' && minY < 0.01) minY = 0; // fix floating point error
  }

  const options: ChartOptions<'line'> = {
    spanGaps: true,
    responsive: true,
    interaction: {
      mode: 'nearest' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        display: legendDisplay,
      },
      title: {
        display: false,
        text: 'Measurement time',
      },
      tooltip: {
        enabled: true,
      }
    },
    scales: {
      x: {
        type: 'time',
        min : startingPoint.toISOString(),
        max : endPoint.toISOString(),
        time: {
          unit:  selectedOption === "Custom" && customTimeUnit
                   ? customTimeUnit
                   : selectedOption === "Last Hour" ? 'minute'
                   : selectedOption === "Last Day"  ? 'hour'
                   : 'day',
          displayFormats: {
            minute: 'HH:mm',
            hour  : 'HH:mm',
            day   : 'dd MMM',
            month : 'MMM yyyy',
            year  : 'yyyy',
            // override on custom
            ...(selectedOption === "Custom" && customTimeUnit
              ? { [customTimeUnit]: customFmt }
              : {}),
          },
        }
      },
      y: {
        min: minY,
        max: maxY,
        title: {
          display: true,
          text: measurementMap[selectedMeasurement],
          font: {
            size: 14
          }
        }
      },
    },
  }


  const chartData = { datasets };


  return <Line options={options} data={chartData} />
}