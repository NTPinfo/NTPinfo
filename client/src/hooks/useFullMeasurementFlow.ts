import { useState, useEffect } from "react";
import { useTriggerMeasurement } from "./useTriggerFullMeasurement";
import { usePollPartialMeasurement } from "./usePollPartialMeasurement";
import { usePollFullMeasurement } from "./usePollFullMeasurement";
import { MeasurementRequest } from "../utils/types";

export const useFullMeasurementFlow = (server: string, payload : MeasurementRequest) => {
    const [started, setStarted] = useState(false);

    const {
        triggerMeasurement,
        measurementId,
        status: triggerStatus,
        error: triggerError,
    } = useTriggerMeasurement();

    const {
        data: partialData,
        status: partialStatus,
        error: partialError
    } = usePollPartialMeasurement(started ? measurementId : null);

    const {
        ntpData,
        ntsData,
        ripeData,
        versionData,
        status: fullStatus,
        error: fullError,
    } = usePollFullMeasurement(started ? measurementId : null, partialData);

    useEffect(() => {
        const start = async () => {
            if (!payload) return;
            const res = await triggerMeasurement(server, payload);
            if (res?.id) setStarted(true);
        };
        start();
    }, [payload]);

    const status = fullStatus || partialStatus || triggerStatus;
    const error = triggerError || partialError || fullError;

    return {
        status,
        error,
        measurementId,
        ntpData,
        ntsData,
        ripeData,
        versionData,
    }
}