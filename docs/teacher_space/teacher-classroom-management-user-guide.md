
# Classroom Management — User Guide

## Overview

This guide explains how to manage a classroom in Open TutorAI CE. Teachers can create classrooms, add students, run live attendance sessions, post announcements, and see the class as a 3D seating chart. Students can join a classroom with a code, check themselves present during a live session, and read class announcements.

---

## For Teachers

### 1. Teacher Dashboard

When you log in as a teacher you land on the Dashboard, which shows a quick summary of your classrooms and your total student count.

![Teacher Dashboard](screenshots/teacher-dashboard.png)

Click **My Classrooms** in the sidebar to see all your classrooms, or **+ Create Classroom** to start a new one.

![My Classrooms — teacher view](screenshots/teacher-my-classrooms.png)

---

### 2. Create a classroom

Click **+ Create Classroom** on the My Classrooms page. A six-step wizard opens.

**Step 1 — Name & Subject**

Fill in the classroom name, a short description, and choose the subject.

![Create Classroom — Step 1](screenshots/create-classroom-step1.png)

Steps 2–5 ask for the course, objectives, level, and other details. When you reach **Step 6 — Review**, you see a summary of everything before confirming.

![Create Classroom — Review (step 6)](screenshots/create-classroom-review.png)

Click **Create Classroom** to finish. You are taken directly to the new classroom's detail page.

---

### 3. Edit or delete a classroom

From the classroom detail page, use the **Edit** and **Delete** buttons in the top-right corner.

**Edit** opens a form pre-filled with the current values:

![Edit Classroom form](screenshots/edit-classroom.png)

**Delete** asks for confirmation and lists exactly what will be removed:

![Delete Classroom confirmation](screenshots/delete-classroom-dialog.png)

---

### 4. Add students to your classroom

Open the **Students** tab. When no students are enrolled yet, you see an empty state:

![Students tab — empty](screenshots/students-tab-empty.png)

You have three options:

- **Add by email** — type a student's email in the top bar and click **Add Student**. The student must already have an account. Use **+ Create Student** to create an account on the spot.
- **Import a CSV** — prepare a file with the columns `email`, `name`, `password` (password is optional). Choose the file and click **Upload**. The result shows how many students were created, enrolled, or skipped.
- **Share the permanent join code** — the permanent join code is shown at the top of the classroom page. Copy and share it with your students. It never expires and has no use limit.
- **Create a one-off invite code** — click **+ New Invite** to generate a temporary code with an optional expiry date and a maximum number of uses. This is useful when you want to control access for a specific enrollment window. Once redeemed the required number of times or past its expiry date, the code stops working.

Once students are enrolled, the list view shows names, emails, and enrollment dates:

![Students tab — list view](screenshots/students-list.png)

---

### 5. View the 3D seating chart

Switch from **List** to **Classroom view** on the Students tab. Three layout buttons appear above the scene.

**Rows** — desks facing the board in a classic row arrangement:

![3D seating chart — rows layout](screenshots/3d-chart-rows.png)

**U-shape** — desks arranged in a U around the board:

![3D seating chart — U layout](screenshots/3d-chart-u.png)

**Islands (groups)** — clusters of four desks, ideal for group work:

![3D seating chart — islands/groups layout](screenshots/3d-chart-islands.png)

Drag to rotate the view and scroll to zoom. Hover over a student's avatar to see their name; click to open their info card.

---

### 6. Start a live attendance session

Go to the **Attendance** tab. When no session has run yet, the counters all show zero:

![Attendance tab — empty state](screenshots/presences-tab-empty.png)

Click **Start a session**. A modal opens where you enter the course name and the objectives for this session:

![Start Session modal](screenshots/start-session-modal.png)

Click **Start Session**. A confirmation screen shows the course, start time, and objectives:

![Session started confirmation](screenshots/session-started-confirmation.png)

Close the modal. The session now appears in the session list. All enrolled students start out marked **Absent** — they become **Present** by joining the session themselves.

---

### 7. View attendance, override a status, and view student history

Click a session in the list. The right panel shows every student and their status (Present / Absent / Late).

**Manually override a student's status** — click the status badge next to any student to cycle through Present → Late → Absent → Present. Changes are saved immediately. This lets you correct mistakes (e.g. a student forgot to check in but was physically present).

Click a student's name to open their attendance history (presence %, absence %, last 10 sessions):

![Attendance list with student history](screenshots/attendance-with-student-history.png)

---

### 8. End and delete a session

- Click the **stop icon** next to an in-progress session to end it. Once ended, students can no longer join.
- Once ended, a **trash icon** appears — click it to permanently delete the session and its attendance records (a confirmation prompt appears).

---

### 9. Post and delete announcements

Go to the **Overview** tab, type a message in the announcement box, and click **Post**. The announcement appears at the top of the stream for all enrolled students.

**Delete an announcement** — click the **trash icon** next to any announcement you posted. The announcement is removed immediately for all users. Only the classroom owner can delete announcements.

---

## For Students

### 1. My Classrooms page

Students see all their enrolled classrooms on the **My Classrooms** page. Classrooms with an open attendance session show a green **Live** badge and a **Join Session** button:

![Student My Classrooms page](screenshots/student-my-classrooms.png)

### 2. Join a live session (mark yourself present)

Click **Join Session** on a Live classroom card. Once you join, the card confirms your attendance:

![Student card — "You are present ✓"](screenshots/student-card-present.png)

If the session has ended, the button is hidden and the Live badge disappears.

### 3. Join a classroom with a code

On the My Classrooms page, enter the code your teacher shared in the **"Join a classroom with a code"** field and click **Join**.
