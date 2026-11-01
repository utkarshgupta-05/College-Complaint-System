# Auxiliary External Evaluation: Real-World Student Complaint Clustering

> **Dataset:** `sanchit-19/university-students-complaints` (Hugging Face, CC-BY-4.0)
> **Sample Size Evaluated:** N=273 student complaints
> **Role:** Zero-Shot External Evaluation (No retraining, strictly isolated from model training)

## 1. Domain & Provenance Notes

- **Student Origin:** 6 university departments with 73.8% CSE representation.
- **Categories:** 5 coarse buckets (`Infrastructure`, `Technical`, `Academic`, `Finance`, `Administrative`).
- **Vocabulary Shift:** Features South Asian campus vernacular (*ShaPa day*, *bKash*, *lift queues*, *prayer room requests*).

## 2. K-Means (k=5) External Evaluation

- **Silhouette Score (Cosine):** 0.049
- **Davies-Bouldin Index:** 4.2788

### Discovered Theme 0 (Size: 186)
- **Top Keywords:** `parking, look, students, campus, classroom, affecting, regular, does`
- **Ground-Truth Categories in Cluster:** {"Infrastructure": 72, "Technical": 50, "Academic": 39, "Administrative": 18, "Finance": 7}
- **Responsible Departments in Cluster:** {"Maintenance": 50, "IT": 45, "Department Head": 42, "Transport & Parking": 20, "Student Welfare": 12, "Proctorial": 6, "Library": 4, "Registrar": 3, "Canteen": 3, "Finance": 1}
- **Sample Real Complaints:**
  - *"Air conditioning in the auditorium stops suddenly."*
  - *"Campus WiFi does not work in all areas and is also very slow. This is affecting regular activities."*

### Discovered Theme 1 (Size: 21)
- **Top Keywords:** `washrooms, hand, female washrooms, wash, hand wash, wash washrooms, new, ones`
- **Ground-Truth Categories in Cluster:** {"Infrastructure": 21}
- **Responsible Departments in Cluster:** {"Maintenance": 21}
- **Sample Real Complaints:**
  - *"The exhaust fans in the washrooms and other areas should be repaired or replaced with new ones. This is affecting regular activities."*
  - *"The exhaust fans in the washrooms and other areas should be repaired or replaced with new ones."*

### Discovered Theme 2 (Size: 20)
- **Top Keywords:** `facilities, need, university, experienced professors, facilities university, experienced, research facilities, professors`
- **Ground-Truth Categories in Cluster:** {"Academic": 8, "Infrastructure": 4, "Technical": 4, "Finance": 4}
- **Responsible Departments in Cluster:** {"Department Head": 8, "Finance": 4, "IT": 4, "Student Welfare": 3, "Maintenance": 1}
- **Sample Real Complaints:**
  - *"We need more research facilities in our university and also we need more experienced professors"*
  - *"We need more research facilities in our university and also we need more experienced professors"*

### Discovered Theme 3 (Size: 29)
- **Top Keywords:** `room, library, needs attention, needs, attention, charging, charging ports, ports`
- **Ground-Truth Categories in Cluster:** {"Infrastructure": 16, "Administrative": 6, "Technical": 4, "Finance": 2, "Academic": 1}
- **Responsible Departments in Cluster:** {"Library": 8, "IT": 7, "Maintenance": 7, "Proctorial": 2, "Student Welfare": 2, "Department Head": 2, "Registrar": 1}
- **Sample Real Complaints:**
  - *"Inadequate Charging ports in library /reading room. Needs attention."*
  - *"Inadequate Charging ports in library /reading room. Kindly verify and take action."*

### Discovered Theme 4 (Size: 17)
- **Top Keywords:** `fee, payment, portal, process, students, takes, long, payment portal`
- **Ground-Truth Categories in Cluster:** {"Finance": 16, "Infrastructure": 1}
- **Responsible Departments in Cluster:** {"Finance": 16, "Transport & Parking": 1}
- **Sample Real Complaints:**
  - *"Fee receipt not issued immediately after payment."*
  - *"Fee portal crashes near payment deadlines."*

## 3. DBSCAN Outlier & Density Analysis

- **Parameters:** `eps=0.55`, `min_samples=3`
- **Coherent Dense Clusters:** 42
- **Noise Complaints Isolated:** 36 (13.2% of corpus)
- **Silhouette Score (non-noise):** 0.5775

### Dense Theme 0 (Size: 3)
- **Keywords:** `parts, parts 8th, floor wifi, 9th floor, 9th, 8th 9th, 8th, wifi`
  - *"On most parts of the 8th/9th floor, WiFi is missing at all."*
  - *"On most parts of the 8th/9th floor, WiFi is unavailable at all. Please look into it."*

### Dense Theme 1 (Size: 51)
- **Keywords:** `wifi, parking, adviser, doesnt, projectors, clear, campus, work`
  - *"CSE Dept doesnt have qualified teachers. Would appreciate a resolution soon."*
  - *"Campus WiFi does not work in all areas and is also very slow. Would appreciate a resolution soon."*

### Dense Theme 2 (Size: 4)
- **Keywords:** `water 6th, longer working, longer, floor cse, drinking water, drinking, dpt longer, dpt`
  - *"drinking water system on the 6th floor(CSE dpt) is no longer working."*
  - *"drinking water system on the 6th floor(CSE dpt) is no longer working. Please look into it."*

### Dense Theme 3 (Size: 4)
- **Keywords:** `maintain concentration, maintain, study maintain, students library, talking students, talking, loud talking, loud`
  - *"Due to continuous loud talking by some students in the library, it has become very difficult to study and maintain concentration"*
  - *"Due to continuous loud talking by some students in the library, it has become very difficult to study and maintain concentration."*

### Dense Theme 4 (Size: 4)
- **Keywords:** `wash washrooms, wash, hand wash, hand, washrooms, washrooms affecting, look, regular activities`
  - *"No hand wash in most of the washrooms"*
  - *"No hand wash in most of the washrooms."*

### Dense Theme 5 (Size: 4)
- **Keywords:** `long line, line lift, line, lift difficult, difficult attend, classes time, attend classes, attend`
  - *"Because of the long line for the lift, it becomes difficult to attend classes on time"*
  - *"Because of the long line for the lift, it becomes difficult to attend classes on time."*

### Dense Theme 6 (Size: 4)
- **Keywords:** `bus, departure, arrival, update, location, arrival departure, know, bus arrival`
  - *"I have complain regarding the routing system of the bus.... Students go through a lot of problems to track location of the bus during arrival and departure . We know we have a msngr group where sometimes update is given but sometimes there is no update so it's a hassle... I would be better if and app system is give to know about the location of the bus upon arrival and departure. As during departure the bus doesn't always remain in same place as a result students get confused"*
  - *"I have complain regarding the routing system of the bus.... Students go through a lot of problems to track location of the bus during arrival and departure . We know we have a msngr group where sometimes update is given but sometimes there is no update so it's a hassle... I would be better if and app system is give to know about the location of the bus upon arrival and departure. As during departure the bus doesn't always remain in same place as a result students get confused."*

### Dense Theme 7 (Size: 5)
- **Keywords:** `ports, charging ports, charging, ports library, reading room, reading, library reading, inadequate charging`
  - *"Inadequate Charging ports in library /reading room"*
  - *"Inadequate Charging ports in library /reading room."*

### Dense Theme 8 (Size: 8)
- **Keywords:** `research facilities, professors, facilities university, experienced professors, experienced, research, facilities, need`
  - *"We need more research facilities in our university and also we need more experienced professors"*
  - *"We need more research facilities in our university and also we need more experienced professors"*

### Dense Theme 9 (Size: 4)
- **Keywords:** `insufficient signal, coverage, coverage insufficient, speed coverage, does reach, fi speed, reach inside, reach`
  - *"Campus Wi-Fi speed and coverage are insufficient; the signal does not reach inside classrooms."*
  - *"Campus Wi-Fi speed and coverage are insufficient; the signal does not reach inside classrooms. Needs attention."*

### Dense Theme 10 (Size: 4)
- **Keywords:** `resolution display, properly causes, lectures, issues lectures, issues, display colors, display, colors properly`
  - *"Projectors have subpar resolution and do not display colors properly, which causes issues in several lectures."*
  - *"Projectors have poor resolution and do not display colors properly, which causes issues in several lectures."*

### Dense Theme 11 (Size: 4)
- **Keywords:** `properly maintained, maintained, regarding timely, repairs, little concern, little, maintained faulty, timely repairs`
  - *"Classroom lights and ACs are not properly maintained; some are faulty, and there appears to be little concern regarding timely repairs."*
  - *"Classroom lights and ACs are not properly maintained; some are faulty, and there appears to be little concern regarding timely repairs. Please look into it."*

### Dense Theme 12 (Size: 4)
- **Keywords:** `resulting, causing inconvenience, cables theory, loss, lecture time, inconvenience faculty, inconvenience, hdmi cables`
  - *"HDMI cables in theory classrooms are mostly faulty, causing inconvenience for faculty members and resulting in loss of lecture time."*
  - *"HDMI cables in theory classrooms are mostly faulty, causing inconvenience for faculty members and resulting in loss of lecture time. Please look into it."*

### Dense Theme 13 (Size: 4)
- **Keywords:** `overcrowded peak, study room, spaces insufficient, remain overcrowded, room spaces, insufficient remain, library study, overcrowded`
  - *"Library and study room spaces are insufficient and remain overcrowded during peak hours."*
  - *"Library and study room spaces are insufficient and remain overcrowded during peak hours. This is affecting regular activities."*

### Dense Theme 14 (Size: 4)
- **Keywords:** `library, making library, learning making, making, learning, occupancy library, student occupancy, severely disrupts`
  - *"When student occupancy at the library increases, the Wi-Fi connection becomes very slow and frequently disconnects. This severely disrupts academic activities, research work,and online learning, making the library ineffective as a study environment during peak hours. Kindly verify and take action."*
  - *"When student occupancy in the library increases, the Wi-Fi connection becomes very slow and frequently disconnects. This severely disrupts academic activities, research work,and online learning, making the library ineffective as a study environment during peak hours. Kindly verify and take action."*

### Dense Theme 15 (Size: 4)
- **Keywords:** `student, student 500taka, studentship certificate, studentship, versity current, versity, student institute, institute`
  - *"A studentship certificate costs a student 500taka which should be of free from the versity as a current student of the institute."*
  - *"A studentship certificate costs a student 500taka which should be of free from the versity as a current student of the institute. Please look into it."*

### Dense Theme 16 (Size: 8)
- **Keywords:** `female washrooms, female, washrooms, floor, male female, floor separate, separate male, separate`
  - *"Every floor should have separate male and female washrooms. Kindly verify and take action."*
  - *"Every floor should have separate male and female washrooms."*

### Dense Theme 17 (Size: 4)
- **Keywords:** `department, space, prayer mechanical, space provided, space prayer, mechanical, like space, like`
  - *"Just like there is a space for prayer in front of the Mechanical Department, a similar space should be provided in front of almost every department for prayers."*
  - *"Just like there is a space for prayer in front of the Mechanical Department, a similar space should be provided in front of almost every department for prayers. Please look into it."*

### Dense Theme 18 (Size: 4)
- **Keywords:** `nagad merchant, nagad, merchant, inside university, good bkash, good, bkash nagad, bkash`
  - *"It would be good if there is a bKash or Nagad merchant in service inside the university."*
  - *"It would be good if there is a bKash or Nagad merchant available inside the university."*

### Dense Theme 19 (Size: 4)
- **Keywords:** `participate curricular, students unwilling, seniors students, seniors, pressure applied, pressure, participate, unwilling facing`
  - *"Pressure is applied to participate in co-curricular activities by seniors, even if students are unwilling or facing problems."*
  - *"Pressure is applied to participate in co-curricular activities by seniors, even if students are unwilling or facing problems. Needs attention."*

### Dense Theme 20 (Size: 4)
- **Keywords:** `7th, 7th floor, class, wi, fi, wi fi, student, floor`
  - *"The 7th floor (6 of lift) does not have Wi-Fi routers. Thus the Wi-Fi connection disappears when a student enters a classroom in the 7th floor. This is extremely inconvenient as it can cause a student to miss their attendance in their class for the lack of internet connectivity despite being present in the class."*
  - *"The 7th floor (6 of lift) does not have Wi-Fi routers. Thus the Wi-Fi connection disappears when a student enters a classroom in the 7th floor. This is extremely inconvenient as it can cause a student to miss their attendance in their class for the lack of internet connectivity despite being present in the class. Please look into it."*

### Dense Theme 21 (Size: 4)
- **Keywords:** `allocate time, prayers lunch, time prayers, routine does, routine, lunch, does allocate, allocate`
  - *"The routine does not allocate time for prayers and lunch."*
  - *"The routine does not allocate time for prayers and lunch. Please look into it."*

### Dense Theme 22 (Size: 4)
- **Keywords:** `equipment, sufficient equipment, sufficient, labs sufficient, equipment does, equipment cases, cases equipment, cases`
  - *"Some labs do not have sufficient equipment, and in many cases, the equipment does not work properly."*
  - *"Some labs do not have sufficient equipment, and in many cases, the equipment does not work properly. Please look into it."*

### Dense Theme 23 (Size: 4)
- **Keywords:** `function entire, function, fi does, entire campus, entire, does function, wi, wi fi`
  - *"Besides, the Wi-Fi does not function well across the entire campus."*
  - *"Besides, the Wi-Fi does not function well across the entire campus. Please look into it."*

### Dense Theme 24 (Size: 4)
- **Keywords:** `loudly, microphones, speak loudly, speak, voices heard, voices, loudly difficult, faculties voices`
  - *"Faculties whose voices cannot be heard loudly or find it difficult to speak loudly in large classrooms should use personal headset microphones for their ease as well as ours."*
  - *"Faculties whose voices cannot be heard loudly or find it difficult to speak loudly in large classrooms should use personal headset microphones for their ease as well as ours. Please look into it."*

### Dense Theme 25 (Size: 4)
- **Keywords:** `glass, transparent glass, transparent, replaced non, lower floors, glass especially, glass washroom, lower`
  - *"The transparent glass of washroom windows should be replaced with non-transparent glass, especially in lower floors, as it is a matter of privacy."*
  - *"The transparent glass of washroom windows should be replaced with non-transparent glass, especially in lower floors, as it is a matter of privacy. This is affecting regular activities."*

### Dense Theme 26 (Size: 3)
- **Keywords:** `teacup, size teacup, size, teacup cafeteria, larger, cafeteria larger, cafeteria, look`
  - *"The size for the teacup in the cafeteria should be larger."*
  - *"The size for the teacup at the cafeteria should be larger."*

### Dense Theme 27 (Size: 4)
- **Keywords:** `shapa, semester, midterm exams, week semester, week, exams, season, midterm`
  - *"The ShaPa day should be organized every semester within 2-3 weeks after midterm exams. ShaPa being in the last week of the semester amidst lab finals and quizzes is not student friendly. Furthermore, if ShaPa is organized within 8th-10th week this semester, then it can be during the spring season i.e. before the unpredictable heat and rain of the summer season starts. The date of the day should also be fixed right after midterm exams so that students can organize their quizzes around that date."*
  - *"The ShaPa day should be organized every semester within 2-3 weeks after midterm exams. ShaPa being at the last week of the semester amidst lab finals and quizzes is not student friendly. Furthermore, if ShaPa is organized within 8th-10th week this semester, then it can be during the spring season i.e. before the unpredictable heat and rain of the summer season starts. The date of the day should also be fixed right after midterm exams so that students can organize their quizzes around that date."*

### Dense Theme 28 (Size: 4)
- **Keywords:** `ended, frequently ended, 1206 course, significantly earlier, significantly, ended significantly, 1206, earlier allocated`
  - *"In the CSE 1206 course, classes are frequently ended significantly earlier than the allocated time."*
  - *"In the CSE 1206 course, classes are frequently ended significantly earlier than the allocated time. Please look into it."*

### Dense Theme 29 (Size: 4)
- **Keywords:** `architecture, washrooms architecture, stairs repaired, lights university, round tube, round, tube, university especially`
  - *"The round tube lights in the university, especially those in the washrooms and on the Architecture stairs, should be repaired or replaced with new ones."*
  - *"The round tube lights at the university, especially those at the washrooms and on the Architecture stairs, should be repaired or replaced with new ones. Please look into it."*

### Dense Theme 30 (Size: 4)
- **Keywords:** `fans washrooms, exhaust fans, exhaust, areas repaired, washrooms areas, fans, replaced new, repaired replaced`
  - *"The exhaust fans in the washrooms and other areas should be repaired or replaced with new ones."*
  - *"The exhaust fans at the washrooms and other areas should be repaired or replaced with new ones."*

### Dense Theme 31 (Size: 4)
- **Keywords:** `day, problems iums, server problems, server, result publication, publication day, publication, wait day`
  - *"Due to server problems in the IUMS system, I was unable to check my result on the publication day and had to wait until the next day"*
  - *"Due to server problems in the IUMS system, I was unable to check my result on the publication day and had to wait until the next day."*

### Dense Theme 32 (Size: 4)
- **Keywords:** `group, teachers students, selected teachers, students groups, selected, projects, members group, suffer`
  - *"The group members for group projects should be selected by the teachers. The students with no groups have to suffer"*
  - *"The group members for group projects should be selected by the teachers. The students with no groups have to suffer."*

### Dense Theme 33 (Size: 4)
- **Keywords:** `talk way, talk, think talk, way want, way, want girls, want, think`
  - *"Some boys think they can talk in whatever way they want with the girls ."*
  - *"Some boys think they can talk in whatever way they want with the girls . Please look into it."*

### Dense Theme 34 (Size: 4)
- **Keywords:** `substantial fees, organizer, required pay, required, students required, organizer event, substantial, pay substantial`
  - *"I am dissatisfied because students are required to pay substantial fees by the organizer, even if they do not take part in the event."*
  - *"I am dissatisfied because students are required to pay substantial fees by the organizer, even if they do not take part in the event. Please look into it."*

### Dense Theme 35 (Size: 4)
- **Keywords:** `groups, teacher assigned, teacher, leads conflicts, leads, groups avoid, forming groups, forming`
  - *"Forming groups ourselves often leads to conflicts. It would be better if the teacher assigned the groups first to avoid any problems."*
  - *"Forming groups ourselves regularly leads to conflicts. It would be better if the teacher assigned the groups first to avoid any problems."*

### Dense Theme 36 (Size: 4)
- **Keywords:** `levels sets, difficulty levels, easy, evaluate, evaluate students, students fairly, fairly, fairly quizzes`
  - *"It is difficult to evaluate students fairly when quizzes have uneven difficulty levels, with some sets being hard and others easy."*
  - *"It is difficult to evaluate students fairly when quizzes have uneven difficulty levels, with some sets being hard and others easy. This is affecting regular activities."*

### Dense Theme 37 (Size: 4)
- **Keywords:** `perform better, perform, quizzes resources, resources struggle, resources, feels unfair, struggle, feels`
  - *"It feels unfair that students with access to alternative sections or materials can perform better in quizzes, while others without these resources struggle."*
  - *"It feels unfair that students with access to alternative sections or materials can perform better in quizzes, while others without these resources struggle. This is affecting regular activities."*

### Dense Theme 38 (Size: 4)
- **Keywords:** `power, generator, lab, room, floors, does`
  - *"Backup generator failed during a recent power cut."*
  - *"Power supply in the seminar room is unstable."*

### Dense Theme 39 (Size: 3)
- **Keywords:** `loose, multiple, payment, power`
  - *"Projector power outlets are loose in multiple rooms."*
  - *"Some stair railings are loose."*

### Dense Theme 40 (Size: 18)
- **Keywords:** `fee, near, payment, portal, broken, process, takes, payment portal`
  - *"Fee portal crashes near payment deadlines."*
  - *"Fee receipt not issued immediately after payment."*

### Dense Theme 41 (Size: 6)
- **Keywords:** `parking, parking area, area, parking areas, motorcycle, motorcycle parking, poor, areas`
  - *"Motorcycle parking area is overcrowded."*
  - *"Parking area lighting is very poor at night."*

