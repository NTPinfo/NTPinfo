import { MeasurementStep } from '../hooks/usePollIncrementalMeasurement';
import '../styles/MeasurementStatusIndicator.css';

interface MeasurementStatusIndicatorProps {
  status: MeasurementStep | null;
  isLoading: boolean;
}

const getStatusMessage = (status: MeasurementStep | null): string => {
  if (!status) return "Initializing measurement...";
  
  switch (status) {
    case "pending":
      return "Measurement pending...";
    case "starting RIPE measurement":
      return "Starting RIPE Atlas measurement...";
    case "adding ntp measurements":
      return "Performing NTP measurements...";
    case "adding nts":
      return "Performing NTS measurement...";
    case "analyzing ntp versions":
      return "Analyzing NTP versions...";
    case "finished":
      return "Measurement completed!";
    case "failed":
      return "Measurement failed";
    default:
      return `Status: ${status}`;
  }
};

const getStatusIcon = (status: MeasurementStep | null, isLoading: boolean): string => {
  if (status === "finished") return "✓";
  if (status === "failed") return "✗";
  if (isLoading || status) return "⟳";
  return "○";
};

export default function MeasurementStatusIndicator({ status, isLoading }: MeasurementStatusIndicatorProps) {
  // Don't show the indicator when measurement is finished
  if (status === "finished") {
    return null;
  }
  
  const message = getStatusMessage(status);
  const icon = getStatusIcon(status, isLoading);
  const isFailed = status === "failed";
  
  return (
    <div className={`measurement-status-indicator ${isFailed ? 'failed' : ''}`}>
      <span className="status-icon">{icon}</span>
      <span className="status-message">{message}</span>
    </div>
  );
}

