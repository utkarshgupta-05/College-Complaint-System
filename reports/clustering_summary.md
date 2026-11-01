# Phase 7: Recurring-Issue Discovery and Pattern Analysis — Validation Summary

> **Validation Dataset:** `data/processed/val.csv` (N=183)
> **Evaluation Date:** 2026-10-30

## 1. Spatiotemporal & Hotspot Analysis

- **Trend Sufficiency Assessment:** Observation window (284 days, N=183) is insufficient to infer seasonal or annual cyclical trends. Claims of seasonality are statistically unsupported.
- **Date Range:** 2026-01-13 to 2026-10-25 (284 days)

### Top Recurring Hotspots (Location + Category)

| location | category | count | percentage |
| --- | --- | --- | --- |
| Sports Complex - Indoor Badminton Court | C07 | 5 | 2.73 |
| Academic Block 2 - Chemistry Lab | C10 | 3 | 1.64 |
| Administrative Block - Registrar Office | C03 | 3 | 1.64 |
| Campus Health Center | C04 | 3 | 1.64 |
| Central Library - Ground Floor | C02 | 3 | 1.64 |
| Academic Block 2 - Physics Lab | C07 | 3 | 1.64 |
| Computer Center - Lab 102 | C03 | 3 | 1.64 |
| Computer Center - Lab 102 | C10 | 3 | 1.64 |

---

## 2. K-Means Parameter Tuning & Selection (E8)

| k | inertia | silhouette_score | davies_bouldin_index |
| --- | --- | --- | --- |
| 3.0 | 168.32547671450016 | 0.0362 | 5.7698 |
| 4.0 | 165.077853065458 | 0.047 | 5.2577 |
| 5.0 | 161.94011551397907 | 0.0514 | 5.0837 |
| 6.0 | 159.43455143379148 | 0.0547 | 4.3667 |
| 7.0 | 155.94720700672434 | 0.0669 | 4.4312 |
| 8.0 | 152.8564353027326 | 0.0789 | 4.2217 |
| 9.0 | 152.11380401378614 | 0.0729 | 3.9065 |
| 10.0 | 149.11138947380888 | 0.0863 | 3.7126 |
| 11.0 | 146.98578282920735 | 0.0769 | 3.558 |
| 12.0 | 144.6815408991036 | 0.0941 | 3.1973 |

**Selected Configuration:** $k=12$, Silhouette Score = **0.0941**, Davies-Bouldin Index = **3.1973**

### Discovered K-Means Clusters

#### Cluster 0: Unnamed Cluster (Size: 25)
- **Top Keywords:** `seriously time, seriously, hope, hope administration, administration, takes seriously, administration takes, time`
- **Category Breakdown:** {"C05": 4, "C02": 4, "C10": 4, "C06": 3, "C07": 3, "C04": 2, "C03": 2, "C08": 1, "C01": 1, "C11": 1}
- **Representative Complaints:**
  - *"Attention maintanance Team: Administrative counter 4 closes 30 minutes before official working hours every day with no substitute staff. Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate. Hope the administration takes this seriously this time."*
  - *"Wanted to bring to your immediate notice that Hostel study room lights are flickering constantly, making it impossible to prepare for mid-semester exams. Hope the administration takes this seriously this time."*

#### Cluster 1: Unnamed Cluster (Size: 18)
- **Top Keywords:** `daily, block, hostel, severely, hostel block, studies health, daily studies, studies`
- **Category Breakdown:** {"C08": 5, "C05": 4, "C04": 2, "C01": 2, "C02": 2, "C03": 1, "C07": 1, "C11": 1}
- **Representative Complaints:**
  - *"Regarding Hostel Block A - Floor 3: female students reported repeated verbal catcalling and harassment by men on motorbikes near hostel block a - floor 3. Still not resolved. This is severely affecting our daily studies and health."*
  - *"Regarding Cafeteria & Canteen: internal assessment marks for practical lab entered as 0/30 due to teacher data entry error. Still not resolved. This is severely affecting our daily studies and health."*

#### Cluster 2: Unnamed Cluster (Size: 27)
- **Top Keywords:** `person, yesterday technician, person yesterday, informed caretaker, caretaker person, technician, technician turned, informed`
- **Category Breakdown:** {"C06": 6, "C08": 6, "C11": 4, "C10": 4, "C07": 2, "C03": 2, "C05": 1, "C01": 1, "C09": 1}
- **Representative Complaints:**
  - *"Wanted to bring to your immediate notice that Proxy server configuration for library e-resources fails with 502 Bad Gateway error. We informed the caretaker in person yesterday but no technician turned up. Kindly take necessary action immediately."*
  - *"Frustrated to report that No-dues clearance portal for graduating batch has multiple bogus pending library dues of Rs. 0. We informed the caretaker in person yesterday but no technician turned up. Thank you."*

#### Cluster 3: Unnamed Cluster (Size: 12)
- **Top Keywords:** `department, resolution, concerned department, concerned, prompt resolution, prompt, expecting prompt, resolution concerned`
- **Category Breakdown:** {"C01": 3, "C03": 2, "C04": 2, "C11": 2, "C10": 1, "C06": 1, "C07": 1}
- **Representative Complaints:**
  - *"Ambiguous complnt: Everything in our department is chaotic and nobody takes responsibility for anything. Expecting a prompt resolution from the concerned department."*
  - *"LAN port at desk in room 312 is dead. Cable tested and working fine elsewhere. Expecting a prompt resolution from the concerned department."*

#### Cluster 4: Unnamed Cluster (Size: 18)
- **Top Keywords:** `disappointing, disappointing state, extremely, extremely disappointing, state, state affairs, affairs, center`
- **Category Breakdown:** {"C04": 4, "C10": 3, "C09": 3, "C06": 3, "C03": 2, "C02": 2, "C07": 1}
- **Representative Complaints:**
  - *"Drinking wtr dispenser in mess hall has slimy green algae deposit around the dispensing nozzle. Many students in Campus Health Center are facing this. Extremely disappointing state of affairs."*
  - *"Frustrated to report that Drinking water dispenser in mess hall has slimy green algae deposit around the dispensing nozzle. Extremely disappointing state of affairs."*

#### Cluster 5: Unnamed Cluster (Size: 14)
- **Top Keywords:** `affecting, studies, daily studies, severely affecting, studies health, affecting daily, severely, daily`
- **Category Breakdown:** {"C09": 3, "C02": 3, "C04": 2, "C07": 2, "C10": 1, "C11": 1, "C03": 1, "C01": 1}
- **Representative Complaints:**
  - *"Wanted to bring to your immediate notice that Campus Wi-Fi authentication portal (captive login) keeps timing out and dropping connection every 10 minutes. Several students residing in this wing have signed a joint complaint about this issue. This is severely affecting our daily studies and health."*
  - *"Wanted to bring to your immediate notice that Fly infestation in the dining area of Hostel Block C (Girls) - Wing 1. Swarms of flies landing directly on open food containers. Several students residing in this wing have signed a joint complaint about this issue. This is severely affecting our daily studies and health."*

#### Cluster 6: Unnamed Cluster (Size: 15)
- **Top Keywords:** `students, affected problem, students affected, problem, affected, minutes, completely, authorities`
- **Category Breakdown:** {"C03": 3, "C04": 3, "C06": 2, "C01": 2, "C09": 2, "C07": 1, "C11": 1, "C05": 1}
- **Representative Complaints:**
  - *"Writing to urgently report that Food ran out completely 45 minutes before the scheduled dinner closing time, leaving over 50 students hungry. Several students are affected by this problem."*
  - *"Respected Authorities, please note that Security guard at vehicle gate refuses helmet-wearing students entry unless they show physical paper pass. Several students are affected by this problem."*

#### Cluster 7: Unnamed Cluster (Size: 15)
- **Top Keywords:** `quick, quick fix, looking, looking forward, forward, forward quick, fix, gate`
- **Category Breakdown:** {"C08": 4, "C07": 3, "C09": 2, "C04": 2, "C06": 2, "C05": 1, "C02": 1}
- **Representative Complaints:**
  - *"Frustrated to report that Broken glass bottles scattered across the basketball court posing injury hazard to players. Looking forward to a quick fix."*
  - *"CCTV security camera covering the bicycle parking and hostel back gate is visibly disconnected. Looking forward to a quick fix."*

#### Cluster 8: Unnamed Cluster (Size: 8)
- **Top Keywords:** `battery, battery operated, campus rickshaw, operated campus, operated, notification, notification replacement, schedule`
- **Category Breakdown:** {"C09": 7, "C11": 1}
- **Representative Complaints:**
  - *"Kindly look into this issue: Battery-operated campus e-rickshaw service has been suspended without notification or replacement schedule. This has been happening repeatedly since last Monday. Looking forward to a quick fix."*
  - *"Kindly look into this issue: Battery-operated campus e-rickshaw service has been suspended without notification or replacement schedule. This has been happening repeatedly since last Friday. Several students are affected by this problem."*

#### Cluster 9: Unnamed Cluster (Size: 20)
- **Top Keywords:** `academic block, room, academic, lab, student, block, portal, attendance`
- **Category Breakdown:** {"C07": 4, "C05": 4, "C02": 3, "C10": 3, "C03": 3, "C08": 2, "C01": 1}
- **Representative Complaints:**
  - *"Attendance percentage on student ERP portal shows 68% whereas physical register attendance is 86%. Thank you."*
  - *"Writing to urgently report that Attendance percentage on student ERP portal shows 68% whereas physical register attendance is 86%. Thank you."*

#### Cluster 10: Unnamed Cluster (Size: 9)
- **Top Keywords:** `told spare, told, approached, approached staff, parts sanctioned, staff told, spare, spare parts`
- **Category Breakdown:** {"C06": 2, "C11": 2, "C01": 1, "C07": 1, "C02": 1, "C03": 1, "C10": 1}
- **Representative Complaints:**
  - *"Writing to urgently report that Whiteboard in classroom 132 is deeply stained and scratched; marker writing cannot be erased. When approached, staff told us that spare parts have not been sanctioned yet."*
  - *"Writing to urgently report that Liquid soap dispensers in all washrooms of academic block have been empty for over two weeks. When approached, staff told us that spare parts have not been sanctioned yet. Several students are affected by this problem."*

#### Cluster 11: Unnamed Cluster *(⚠️ WEAK CLUSTER)* (Size: 2)
- **Top Keywords:** `past midnight, security guards, outsiders, midnight, hostel premises, midnight checked, outsiders entered, premises past`
- **Category Breakdown:** {"C08": 2}
- **Representative Complaints:**
  - *"Wanted to bring to your immediate notice that Unidentified outsiders entered hostel premises past midnight without being checked by security guards. Looking forward to a quick fix."*
  - *"Unidentified outsiders entered hostel premises past midnight without being checked by security guards."*
- **Warning:** Cluster size (n=2) is below minimum support threshold (5); insufficient statistical mass to treat as an established operational trend.


---

## 3. Density-Based Clustering: DBSCAN (E10)

- **Parameters:** `eps=0.58`, `min_samples=3`, `metric=cosine`
- **Discovered Dense Clusters:** 21
- **Noise / Isolated Complaints:** 87 (47.5% of validation corpus)
- **Silhouette (non-noise):** 0.4274

#### Dense Cluster 0 (Size: 3)
- **Top Terms:** `ac, ac outdoor, accumulating window, window sills, breathing, breathing issues, droppings, droppings accumulating`
- **Category Breakdown:** {"C07": 3}
  - *"Urgent grievance: Pigeon droppings accumulating on window sills and AC outdoor units of Sports Complex - Indoor Badminton Court causing breathing issues. Please fix this on priority."*
  - *"Attention Maintenance Team: Pigeon droppings accumulating on window sills and AC outdoor units of Sports Complex - Indoor Badminton Court causing breathing issues. Several students residing in this wing have signed a joint complaint about this issue. Expecting a prompt resolution from the concerned department."*

#### Dense Cluster 1 (Size: 6)
- **Top Terms:** `broken, collar, microphone broken, audio inaudible, row collar, classroom lecture, lecture audio, collar microphone`
- **Category Breakdown:** {"C05": 5, "C07": 1}
  - *"Frustrated to report that Classroom lecture audio is inaudible beyond the third row because the collar microphone is broken. Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate. Expecting a prompt resolution from the concerned department."*
  - *"Severe inconvenience being faced: Classroom lecture audio is inaudible beyond the third row because the collar microphone is broken. Several students are affected by this problem."*

#### Dense Cluster 2 (Size: 3)
- **Top Terms:** `construction noise, sleep meditation, morning sleep, 30 disrupting, new, building, disrupting morning, sleep`
- **Category Breakdown:** {"C11": 3}
  - *"Attention Maintenance Team: Construction noise from new building site starts at 5:30 AM disrupting morning sleep and meditation. This is severely affecting our daily studies and health."*
  - *"Writing to urgently report that Construction noise from new building site starts at 5:30 AM disrupting morning sleep and meditation. Kindly take necessary action immediately."*

#### Dense Cluster 3 (Size: 18)
- **Top Terms:** `students, daily, bring immediate, bring, wanted bring, immediate notice, wanted, immediate`
- **Category Breakdown:** {"C07": 6, "C06": 3, "C02": 2, "C09": 1, "C08": 1, "C11": 1, "C04": 1, "C03": 1, "C10": 1, "C01": 1}
  - *"Wanted to bring to your immediate notice that Fly infestation in the dining area of Hostel Block C (Girls) - Wing 1. Swarms of flies landing directly on open food containers. Several students residing in this wing have signed a joint complaint about this issue. This is severely affecting our daily studies and health."*
  - *"Wanted to bring to your immediate notice that Campus Wi-Fi authentication portal (captive login) keeps timing out and dropping connection every 10 minutes. Several students residing in this wing have signed a joint complaint about this issue. This is severely affecting our daily studies and health."*

#### Dense Cluster 4 (Size: 3)
- **Top Terms:** `vendor overcharging, vendor, printed mrp, overcharging printed, products, packaged biscuits, mrp, packaged`
- **Category Breakdown:** {"C04": 3}
  - *"Canteen vendor is overcharging above printed MRP for packaged biscuits and dairy products."*
  - *"This is the third time I am reporting this. Canteen vendor is overcharging above printed MRP for packaged biscuits and dairy products. Hope the administration takes this seriously this time."*

#### Dense Cluster 5 (Size: 3)
- **Top Terms:** `dispensing, dispensing nozzle, nozzle, slimy green, slimy, hall slimy, green algae, dispenser mess`
- **Category Breakdown:** {"C04": 3}
  - *"Drinking wtr dispenser in mess hall has slimy green algae deposit around the dispensing nozzle. Many students in Campus Health Center are facing this. Extremely disappointing state of affairs."*
  - *"Frustrated to report that Drinking water dispenser in mess hall has slimy green algae deposit around the dispensing nozzle. Extremely disappointing state of affairs."*

#### Dense Cluster 6 (Size: 4)
- **Top Terms:** `turned thank, technician turned, yesterday technician, caretaker person, informed caretaker, informed, person yesterday, technician`
- **Category Breakdown:** {"C10": 1, "C05": 1, "C08": 1, "C03": 1}
  - *"Frustrated to report that No-dues clearance portal for graduating batch has multiple bogus pending library dues of Rs. 0. We informed the caretaker in person yesterday but no technician turned up. Thank you."*
  - *"Smell of burning rubber and chemical smoke emerging from basement electrical control room near Central Library - Reading Hall 2. We informed the caretaker in person yesterday but no technician turned up. Thank you."*

#### Dense Cluster 7 (Size: 4)
- **Top Terms:** `attendance, percentage student, physical register, percentage, student erp, shows 68, register, portal shows`
- **Category Breakdown:** {"C05": 4}
  - *"Attendance percentage on student ERP portal shows 68% whereas physical register attendance is 86%. Thank you."*
  - *"Writing to urgently report that Attendance percentage on student ERP portal shows 68% whereas physical register attendance is 86%. Thank you."*

#### Dense Cluster 8 (Size: 7)
- **Top Terms:** `department, resolution, expecting prompt, prompt, concerned, concerned department, resolution concerned, expecting`
- **Category Breakdown:** {"C03": 2, "C06": 1, "C07": 1, "C11": 1, "C04": 1, "C01": 1}
  - *"Ambiguous complnt: Everything in our department is chaotic and nobody takes responsibility for anything. Expecting a prompt resolution from the concerned department."*
  - *"LAN port at desk in room 312 is dead. Cable tested and working fine elsewhere. Expecting a prompt resolution from the concerned department."*

#### Dense Cluster 9 (Size: 3)
- **Top Terms:** `exactly pm, pm study, hours prior, occur, study hours, notice maintenance, occur day, power cuts`
- **Category Breakdown:** {"C02": 3}
  - *"Power cuts occur every day at exactly 8 PM during study hours without any prior notice from maintenance. Many students in Central Library - Ground Floor are facing this. Please fix this on priority."*
  - *"Regarding Central Library - Ground Floor: power cuts occur every day at exactly 8 pm during study hours without any prior notice from maintenance. Still not resolved. Hope the administration takes this seriously this time."*

#### Dense Cluster 10 (Size: 3)
- **Top Terms:** `room, triple sharing, room allocation, occupancy, paying fee, paying, triple, fee double`
- **Category Breakdown:** {"C01": 3}
  - *"Room allocation issue: assigned a triple-sharing room despite paying full fee for double-occupancy room."*
  - *"Respected Authorities, please note that Room allocation issue: assigned a triple-sharing room despite paying full fee for double-occupancy room. Several students are affected by this problem."*

#### Dense Cluster 11 (Size: 4)
- **Top Terms:** `wrappers mud, corridors staircases, mud, littered, staircases, plastic wrappers, mud construction, corridors`
- **Category Breakdown:** {"C07": 3, "C11": 1}
  - *"Wanted to bring to your immediate notice that Corridors and staircases of Hostel Block B - Floor 2 are littered with plastic wrappers, mud, and construction debris. We informed the caretaker in person yesterday but no technician turned up. This is severely affecting our daily studies and health."*
  - *"Frustrated to report that Corridors and staircases of Hostel Block B - Floor 2 are littered with plastic wrappers, mud, and construction debris. Looking forward to a quick fix."*

#### Dense Cluster 12 (Size: 3)
- **Top Terms:** `registrar office, registrar, block registrar, office, administrative block, administrative, hygiene, block`
- **Category Breakdown:** {"C07": 1, "C04": 1, "C02": 1}
  - *"No running water supply in washrooms of Administrative Block - Registrar Office for over 18 hours. Daily hygiene severely affected."*
  - *"Found a dead cockroach inside the dal served during dinner at Administrative Block - Registrar Office. Severe hygiene violation."*

#### Dense Cluster 13 (Size: 6)
- **Top Terms:** `chargers, frequent, chargers electrical, electrical equipment, voltage fluctuations, laptop, laptop chargers, damaging laptop`
- **Category Breakdown:** {"C02": 4, "C10": 2}
  - *"I am a resident student and Frequent voltage fluctuations in Campus Health Center are damaging laptop chargers and electrical equipment. Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate. Hope the administration takes this seriously this time."*
  - *"I am a resident student and Frequent voltage fluctuations in Hostel Block C (Girls) - Wing 1 are damaging laptop chargers and electrical equipment. This is severely affecting our daily studies and health."*

#### Dense Cluster 14 (Size: 8)
- **Top Terms:** `rickshaw service, rickshaw, battery operated, operated, battery, service, service suspended, schedule`
- **Category Breakdown:** {"C09": 7, "C08": 1}
  - *"Frustrated to report that Battery-operated campus e-rickshaw service has been suspended without notification or replacement schedule. Looking forward to a quick fix."*
  - *"Kindly look into this issue: Battery-operated campus e-rickshaw service has been suspended without notification or replacement schedule. This has been happening repeatedly since last Monday. Looking forward to a quick fix."*

#### Dense Cluster 15 (Size: 3)
- **Top Terms:** `gate visibly, covering bicycle, disconnected, hostel gate, security camera, visibly disconnected, visibly, parking hostel`
- **Category Breakdown:** {"C08": 3}
  - *"I am a resident student and CCTV security camera covering the bicycle parking and hostel back gate is visibly disconnected."*
  - *"CCTV security camera covering the bicycle parking and hostel back gate is visibly disconnected. Looking forward to a quick fix."*

#### Dense Cluster 16 (Size: 3)
- **Top Terms:** `doors, campus safety, safety regulations, safety, violating, violating campus, outside violating, padlocked outside`
- **Category Breakdown:** {"C08": 3}
  - *"Frustrated to report that Fire exit doors on 3rd floor of Hostel Block C (Girls) - Wing 2 are padlocked from outside, violating campus fire safety regulations. We informed the caretaker in person yesterday but no technician turned up. Kindly take necessary action urgent."*
  - *"This is the third time I am reporting this. Fire exit doors on 3rd floor of Mess Hall 2 (South Dining) are padlocked from outside, violating campus fire safety regulations. We informed the caretaker in person yesterday but no technician turned up. Looking forward to a quick fix."*

#### Dense Cluster 17 (Size: 3)
- **Top Terms:** `wheeler, wheeler parking, cars parked, completely staff, designated student, lot completely, parking lot, staff cars`
- **Category Breakdown:** {"C09": 3}
  - *"I am a resident student and Designated student two-wheeler parking lot is completely full by 9 AM due to staff cars parked illegally. Looking forward to a quick fix."*
  - *"Severe inconvenience being faced: Designated student two-wheeler parking lot is completely full by 9 AM due to staff cars parked illegally. Extremely disappointing state of affairs."*

#### Dense Cluster 18 (Size: 3)
- **Top Terms:** `female students, men, students reported, verbal catcalling, repeated verbal, repeated, harassment, men motorbikes`
- **Category Breakdown:** {"C08": 3}
  - *"Respected Authorities, please note that Female students reported repeated verbal catcalling and harassment by men on motorbikes near Hostel Block A - Floor 3. Thank you."*
  - *"Regarding Hostel Block A - Floor 3: female students reported repeated verbal catcalling and harassment by men on motorbikes near hostel block a - floor 3. Still not resolved. This is severely affecting our daily studies and health."*

#### Dense Cluster 19 (Size: 3)
- **Top Terms:** `30 teacher, entered 30, marks practical, entry error, internal, practical lab, lab entered, teacher data`
- **Category Breakdown:** {"C05": 3}
  - *"Internal assessment marks for practical lab entered as 0/30 due to teacher data entry error. Thank you."*
  - *"Respected Authorities, please note that Internal assessment marks for practical lab entered as 0/30 due to teacher data entry error. This has been happening repeatedly since last Monday. Thank you."*

#### Dense Cluster 20 (Size: 3)
- **Top Terms:** `ran, food ran, leaving 50, leaving, hungry, 50, 50 students, minutes scheduled`
- **Category Breakdown:** {"C04": 3}
  - *"Urgent grievance: Food ran out completely 45 minutes before the scheduled dinner closing time, leaving over 50 students hungry. Please fix this on priority."*
  - *"Writing to urgently report that Food ran out completely 45 minutes before the scheduled dinner closing time, leaving over 50 students hungry. Several students are affected by this problem."*

