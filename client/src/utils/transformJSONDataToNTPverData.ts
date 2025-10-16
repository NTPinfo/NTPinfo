import { NTPVersionsData } from "./types.ts"

/**
 * Converts a backend NTPVersions JSON object into an NTPVersionsData object.
 * All fields are passed through directly, matching the database columns.
 * Includes linked measurement JSONs if the backend provides them.
 * 
 * @param fetchedData JSON object representing the NTPVersions database model.
 * @returns NTPVersionsData object or null if no data provided.
 */
export const transformJSONDataToNTPVerData = (fetchedData: any): NTPVersionsData | null => {
    if (!fetchedData)
        return null

    return {
        id_vs: fetchedData.id_vs,

        id_v4_1: fetchedData.id_v4_1,
        id_v4_2: fetchedData.id_v4_2,
        id_v4_3: fetchedData.id_v4_3,
        id_v4_4: fetchedData.id_v4_4,
        id_v5: fetchedData.id_v5,

        ntpv1_response_version: fetchedData.ntpv1_response_version,
        ntpv2_response_version: fetchedData.ntpv2_response_version,
        ntpv3_response_version: fetchedData.ntpv3_response_version,
        ntpv4_response_version: fetchedData.ntpv4_response_version,
        ntpv5_response_version: fetchedData.ntpv5_response_version,

        ntpv1_supported_conf: fetchedData.ntpv1_supported_conf,
        ntpv2_supported_conf: fetchedData.ntpv2_supported_conf,
        ntpv3_supported_conf: fetchedData.ntpv3_supported_conf,
        ntpv4_supported_conf: fetchedData.ntpv4_supported_conf,
        ntpv5_supported_conf: fetchedData.ntpv5_supported_conf,

        ntpv1_analysis: fetchedData.ntpv1_analysis,
        ntpv2_analysis: fetchedData.ntpv2_analysis,
        ntpv3_analysis: fetchedData.ntpv3_analysis,
        ntpv4_analysis: fetchedData.ntpv4_analysis,
        ntpv5_analysis: fetchedData.ntpv5_analysis,

        
    }
}