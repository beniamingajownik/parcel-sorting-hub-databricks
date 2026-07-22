# Hub Operations & Processing Analysis

---

## Priority SLA Underperformance

### Finding
Priority parcels are the only service type significantly underperforming the SLA target.

### Evidence
* **Priority SLA:** 84.07%
* **SLA Target:** >90%
* **Gap to Target:** -5.93 percentage points
* **Courier Standard SLA:** 91.83%
* **Locker 24h SLA:** 91.80%
* **Processing Bottlenecks:** The average parcel journey is dominated by the **Inbound-to-Loaded** and **Loading-to-Loaded** stages, which together represent the majority of total processing time.

### Root-Cause Hypothesis
Priority parcels experience excessive waiting time during the outbound loading process, because they follow the same operational flow as standard-service parcels despite having a stricter service-level requirement.

![alt text](/jpg/priority-sla-loading-minutes.png)


### Recommended Action
1. Introduce a dedicated Priority routing path immediately after the inbound scan.
2. Route Priority parcels to dedicated express outbound chutes or sorting lanes.
3. Evaluate the feasibility of dedicated Priority transport capacity for selected routes.
4. If dedicated transport is introduced, reassess the operational cost and Priority service pricing to determine whether the additional cost is commercially justified.

### Expected Impact
* Reduced Loading-to-Loaded processing time for Priority parcels.
* Reduced total Inbound-to-Loaded cycle time.
* Improved Priority SLA performance.
* *Trade-off:* Potentially higher operational cost if dedicated transport capacity is required.

### Validation Method
Conduct a controlled pilot comparing Priority parcels processed through the standard flow against parcels processed through the proposed Priority flow.

**Key Metrics to Measure:**
* Priority SLA %
* Average Loading-to-Loaded minutes
* Average Inbound-to-Loaded minutes
* % of Priority parcels exceeding SLA threshold
* Additional transportation cost per parcel

> **Success Criterion:** The intervention should be considered successful if SLA performance improves toward or above the 90% target without creating an unacceptable increase in cost.

---

## Scan Failures Are Not Primarily Driven by Intake Peaks

### Finding
The volume of failed scans follows the overall parcel intake pattern, but the scan failure rate remains relatively stable throughout the operating day.

### Evidence
* Failed scan volume increases during periods of higher parcel intake.
* The failed scan rate remains approximately **1.5–2%** across the day.
* The pattern does not show a clear proportional deterioration in scan quality during the highest-volume periods.

![alt text](/jpg/total-scans-vs-failed-scans.png)

---

## Employee Exception Resolution Performance Is Close to Target

### Finding
The majority of employees meet the exception-resolution KPI, while employees below target remain relatively close to the required performance level.

### Evidence
* **Target:** >60% of exceptions resolved within 130 minutes
* **Actual:** More than 63% of employees meet the KPI
* **Lowest Observed Performance:** 58.92%
* **Average Resolution Time:** 127.39 minutes *(Target: <130 minutes)*

![alt text](/jpg/employee-time-to-resolve.png)

### Root-Cause Hypothesis
Exception resolution performance appears to be relatively consistent across employees, with no evidence of a large group of severely underperforming employees.

The remaining gap to the KPI may be related to operational differences rather than purely individual employee performance:
* Exception complexity
* Exception type
* Workload and assigned volumes
* Operational conditions

### Recommended Action
1. Identify practices used by employees with consistently higher performance.
2. Provide targeted process guidance or coaching to employees below target.

### Expected Impact
* Increase the proportion of employees meeting the KPI.
* Improve consistency in exception resolution performance.
* Reduce the number of exceptions exceeding the 130-minute resolution threshold.

### Validation Method
Track employee performance over time using:
* % resolved within 130 minutes
* Average resolution time
* Number of assigned exceptions

Compare performance before and after targeted interventions.

---

## Exceptions by Error Code

![alt text](/jpg/exceptions-by-error-code.png)

## Top four error codes in exceptions

### Finding
Top four Error Codes in parcel exceptions come from Scanner device type located in the Inbound zone.

### Evidence
* Blurry Image, Low-Contrast Label, QR Code Damage and Wrong Hub Routing are among the highest-volume scan failure categories.
* The dashboard shows approximately **29.50K - 30.00K exceptions** associated with this error codes.

```
WITH exceptions AS (
    SELECT
        fe.device_id,
        d.type AS device_type,
        d.zone AS device_zone,
        COUNT(*) AS total_exceptions_caused
    FROM parcel_sorting_hub.gold.fact_exceptions fe
    JOIN parcel_sorting_hub.silver.devices d
        ON fe.device_id = d.device_id
    WHERE fe.error_code IN ('BLURRY_IMAGE', 'LOW_CONTRAST_LABEL', 'QR_CODE_DAMAGED', 'WRONG_HUB_ROUTING')
    GROUP BY fe.device_id, d.type, d.zone
),

scans AS (
    SELECT
        device_id,
        COUNT(*) AS total_failed_scans
    FROM parcel_sorting_hub.silver.scans
    GROUP BY device_id
)

SELECT
    e.device_id,
    e.device_type,
    e.device_zone,
    s.total_failed_scans,
    e.total_exceptions_caused,
    ROUND(e.total_exceptions_caused / s.total_failed_scans * 100, 2) AS pct_failed
FROM exceptions e
LEFT JOIN scans s
    ON e.device_id = s.device_id
ORDER BY pct_failed DESC;
```

| device_id | device_type | device_zone | total_failed_scans | total_exceptions_caused | pct_failed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DEV-00039` | `Scanner` | `Inbound` | `185229` | `5638` | `3.04` |
| `DEV-00029` | `Scanner` | `Inbound` | `185640` | `5592` | `3.01` |
| `DEV-00056` | `Scanner` | `Inbound` | `185394` | `5555` | `3.00` |
| `DEV-00013` | `Scanner` | `Inbound` | `185447` | `5554` | `2.99` |
| `DEV-00005` | `Scanner` | `Inbound` | `185883` | `5525` | `2.97` |
| `DEV-00054` | `Scanner` | `Inbound` | `185308` | `5475` | `2.95` |
| DEV-00008 | Scanner | Sort_Area | 131289 | 2019 | 1.54 |
| DEV-00072 | Scanner | Sort_Area | 130584 | 1997 | 1.53 |
| DEV-00051 | Scanner | Sort_Area | 130801 | 1990 | 1.52 |
| DEV-00062 | Dimensioner | Sort_Area | 130726 | 1971 | 1.51 |
| DEV-00015 | Scanner | Sort_Area | 130835 | 1973 | 1.51 |
| DEV-00075 | Dimensioner | Sort_Area | 130481 | 1965 | 1.51 |
| DEV-00073 | Scanner | Sort_Area | 130834 | 1956 | 1.50 |
| DEV-00006 | Dimensioner | Sort_Area | 130885 | 1951 | 1.49 |
| DEV-00034 | Dimensioner | Sort_Area | 130829 | 1948 | 1.49 |
| DEV-00042 | Dimensioner | Sort_Area | 130150 | 1926 | 1.48 |
| DEV-00016 | Scanner | Sort_Area | 130694 | 1929 | 1.48 |
| DEV-00021 | Dimensioner | Sort_Area | 131261 | 1943 | 1.48 |
| DEV-00044 | Dimensioner | Sort_Area | 131348 | 1934 | 1.47 |
| DEV-00053 | Scanner | Sort_Area | 131354 | 1937 | 1.47 |
| DEV-00074 | Scanner | Sort_Area | 130216 | 1877 | 1.44 |
| DEV-00050 | Dimensioner | Inbound | 563397 | 5659 | 1.00 |
| DEV-00043 | Dimensioner | Inbound | 562282 | 5625 | 1.00 |
| DEV-00069 | Dimensioner | Inbound | 561819 | 5581 | 0.99 |
| DEV-00067 | Dimensioner | Inbound | 562430 | 5522 | 0.98 |
| DEV-00024 | Dimensioner | Inbound | 561954 | 5480 | 0.98 |
| DEV-00031 | Dimensioner | Outbound | 313456 | 2394 | 0.76 |
| DEV-00046 | Dimensioner | Outbound | 313924 | 2381 | 0.76 |
| DEV-00071 | Scanner | Outbound | 314737 | 2376 | 0.75 |
| DEV-00047 | Dimensioner | Outbound | 314757 | 2371 | 0.75 |
| DEV-00004 | Dimensioner | Outbound | 314585 | 2367 | 0.75 |
| DEV-00025 | Dimensioner | Outbound | 313645 | 2352 | 0.75 |
| DEV-00022 | Scanner | Outbound | 313811 | 2310 | 0.74 |
| DEV-00064 | Scanner | Outbound | 314079 | 2310 | 0.74 |
| DEV-00060 | Dimensioner | Outbound | 313922 | 2333 | 0.74 |
| DEV-00018 | Dimensioner | Outbound | 314053 | 2309 | 0.74 |
| DEV-00023 | Scanner | Outbound | 315174 | 2297 | 0.73 |
| DEV-00003 | Dimensioner | Outbound | 313555 | 2297 | 0.73 |

### Root-Cause Hypothesis
**Overall potential causes include**:
* Scanner calibration issues or Scanner hardware degradation
* Poor label/barcode design or printing quality.

**QR-code damage** may occur at any point in the chain:
* At the source hub
* During linehaul transportation
* During handling before inbound scanning
* During sorting operations inside the hub

*(The current data does not establish which of these is responsible.)*

### Recommended Action
1. Introduce a QR-code quality inspection at parcel intake and record the result to establish a baseline.
2. Measure **Failure Rate Before vs. After Inspection**

**`If failure rates do not decline significantly after Inspection, then:`**

3. Recalibrate scanning equipment.
4. Test scanner performance before and after recalibration.
5. If the problem persists, investigate scanner hardware and image-processing capabilities.

### Expected Impact
* Reduced Top four scan failures.
* Reduced manual exception volume.
* Improved inbound processing efficiency.
* Potential reduction in exception resolution workload.
* Identification of the stage where QR-code damage is introduced.

---