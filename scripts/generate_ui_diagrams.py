import os
import matplotlib
os.environ['MPLCONFIGDIR'] = os.path.abspath('reports/figures')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_student_portal_ui():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')

    # Header
    rect_hdr = patches.FancyBboxPatch((0.5, 5.2), 10, 0.6, boxstyle='round,pad=0.05', facecolor='#1E293B', edgecolor='none')
    ax.add_patch(rect_hdr)
    ax.text(0.8, 5.5, 'Campus Grievance Portal - Student View', color='#FFFFFF', fontsize=11, fontweight='bold', va='center')
    ax.text(9.5, 5.5, 'Role: Student (STU-001)', color='#94A3B8', fontsize=9, va='center', ha='right')

    # Left Input Panel
    rect_in = patches.FancyBboxPatch((0.5, 0.5), 4.8, 4.4, boxstyle='round,pad=0.1,rounding_size=0.1', facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=1.2)
    ax.add_patch(rect_in)
    ax.text(0.8, 4.5, 'Submit a Complaint', fontsize=12, fontweight='bold', color='#0F172A')

    ax.text(0.8, 4.0, 'Campus Location:', fontsize=9, fontweight='bold', color='#475569')
    rect_loc = patches.Rectangle((0.8, 3.55), 4.2, 0.35, facecolor='#F1F5F9', edgecolor='#CBD5E1')
    ax.add_patch(rect_loc)
    ax.text(1.0, 3.72, 'Hostel Block B - Floor 2', fontsize=8.5, color='#1E293B', va='center')

    ax.text(0.8, 3.25, 'Complaint Description (300 ms debounced):', fontsize=9, fontweight='bold', color='#475569')
    rect_txt = patches.Rectangle((0.8, 1.4), 4.2, 1.7, facecolor='#F8FAFC', edgecolor='#94A3B8')
    ax.add_patch(rect_txt)
    ax.text(1.0, 2.7, 'The ceiling fan in my room is making an\nunusual buzzing noise and vibrating.\nMid-semester exams are approaching...', 
            fontsize=8.5, color='#1E293B', va='top')

    rect_btn = patches.FancyBboxPatch((0.8, 0.75), 4.2, 0.45, boxstyle='round,pad=0.05', facecolor='#2563EB', edgecolor='none')
    ax.add_patch(rect_btn)
    ax.text(2.9, 0.97, 'Submit Complaint', color='#FFFFFF', fontsize=10, fontweight='bold', ha='center', va='center')

    # Right AI Feedback Panel
    rect_out = patches.FancyBboxPatch((5.7, 0.5), 4.8, 4.4, boxstyle='round,pad=0.1,rounding_size=0.1', facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=1.2)
    ax.add_patch(rect_out)
    ax.text(6.0, 4.5, 'Live AI Keystroke Pre-Triage', fontsize=12, fontweight='bold', color='#0F172A')

    # Triage Card
    rect_card = patches.FancyBboxPatch((6.0, 2.7), 4.2, 1.5, boxstyle='round,pad=0.08', facecolor='#EFF6FF', edgecolor='#93C5FD', lw=1.2)
    ax.add_patch(rect_card)
    ax.text(6.2, 3.9, 'Predicted Department:', fontsize=8.5, color='#1E40AF', fontweight='bold')
    ax.text(6.2, 3.55, 'Hostel and Accommodation (C01)', fontsize=10, color='#1E3A8A', fontweight='bold')
    # Confidence bar
    rect_bar_bg = patches.Rectangle((6.2, 3.25), 3.8, 0.18, facecolor='#DBEAFE', edgecolor='none')
    rect_bar_fg = patches.Rectangle((6.2, 3.25), 3.8 * 0.952, 0.18, facecolor='#2563EB', edgecolor='none')
    ax.add_patch(rect_bar_bg)
    ax.add_patch(rect_bar_fg)
    ax.text(6.2, 2.95, 'Confidence: 95.2% (Auto-Routed)', fontsize=8, color='#1E40AF')
    ax.text(9.9, 2.95, 'Priority: LOW (18.5)', fontsize=8, color='#16A34A', fontweight='bold', ha='right')

    # Duplicate Alert
    rect_dup = patches.FancyBboxPatch((6.0, 0.9), 4.2, 1.5, boxstyle='round,pad=0.08', facecolor='#FFFBEB', edgecolor='#FDE68A', lw=1.2)
    ax.add_patch(rect_dup)
    ax.text(6.2, 2.1, 'Advisory Duplicate Alert (Cosine: 0.82)', fontsize=9, color='#B45309', fontweight='bold')
    ax.text(6.2, 1.8, 'Similar issue reported: #CMP-1042', fontsize=8.5, color='#92400E', fontweight='bold')
    ax.text(6.2, 1.45, 'Fan vibrating and regulator broken in B-204\nStatus: IN_PROGRESS | Assigned: Hostel Maintenance', 
            fontsize=7.5, color='#78350F')
    ax.text(6.2, 1.05, 'Advisory Only: You can still submit if this is a separate issue.', fontsize=7, color='#B45309', fontstyle='italic')

    plt.tight_layout()
    fig.savefig('reports/figures/student_portal_ui_flow.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    print('Generated student_portal_ui_flow.png')

def create_staff_admin_ui():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')

    # Header
    rect_hdr = patches.FancyBboxPatch((0.5, 5.2), 10, 0.6, boxstyle='round,pad=0.05', facecolor='#1E293B', edgecolor='none')
    ax.add_patch(rect_hdr)
    ax.text(0.8, 5.5, 'Campus Staff Portal & Explainability Center', color='#FFFFFF', fontsize=11, fontweight='bold', va='center')
    ax.text(9.5, 5.5, 'Role: Staff (Electricity & Water)', color='#94A3B8', fontsize=9, va='center', ha='right')

    # Left: Departmental Queue
    rect_q = patches.FancyBboxPatch((0.5, 0.5), 5.0, 4.4, boxstyle='round,pad=0.1,rounding_size=0.1', facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=1.2)
    ax.add_patch(rect_q)
    ax.text(0.8, 4.5, 'Department Queue (Filtered: C02)', fontsize=11, fontweight='bold', color='#0F172A')

    # Rows in queue
    def draw_row(y, tid, title, pri, pri_color, bg_row='#F8FAFC'):
        r = patches.Rectangle((0.8, y), 4.4, 0.7, facecolor=bg_row, edgecolor='#E2E8F0')
        ax.add_patch(r)
        ax.text(0.95, y + 0.45, f'{tid}: {title}', fontsize=8, fontweight='bold', color='#1E293B')
        p_badge = patches.FancyBboxPatch((4.3, y + 0.35), 0.8, 0.25, boxstyle='round,pad=0.03', facecolor=pri_color, edgecolor='none')
        ax.add_patch(p_badge)
        ax.text(4.7, y + 0.47, pri, fontsize=7, fontweight='bold', color='#FFFFFF', ha='center', va='center')
        ax.text(0.95, y + 0.18, 'Assigned: Electricity | Auto-Routed (98%)', fontsize=7, color='#64748B')

    draw_row(3.6, '#CMP-201', 'Sparking in Chemistry lab switchboard', 'CRITICAL', '#DC2626', '#FEF2F2')
    draw_row(2.7, '#CMP-189', 'Water tank overflow on Hostel 3 roof', 'HIGH', '#EA580C')
    draw_row(1.8, '#CMP-174', 'Water purifier filter dirty in Library', 'MEDIUM', '#D97706')
    draw_row(0.9, '#CMP-152', 'Corridor bulb flickering in Block A', 'LOW', '#16A34A')

    # Right: Explainability & Audit Modal
    rect_mod = patches.FancyBboxPatch((5.9, 0.5), 4.6, 4.4, boxstyle='round,pad=0.1,rounding_size=0.1', facecolor='#FFFFFF', edgecolor='#3B82F6', lw=1.5)
    ax.add_patch(rect_mod)
    ax.text(6.2, 4.5, 'Ticket Explainability & Audit Log', fontsize=11, fontweight='bold', color='#1E3A8A')
    ax.text(6.2, 4.2, 'Inspecting #CMP-201: Sparking in Chemistry lab', fontsize=8, color='#64748B')

    # Section 1: Probability breakdown
    ax.text(6.2, 3.85, '1. Calibrated Model Confidence:', fontsize=8.5, fontweight='bold', color='#334155')
    ax.text(6.2, 3.6, 'C02 Electricity: 88.4% | C06 Lab: 9.2% | C01 Hostel: 1.1%', fontsize=7.5, color='#475569')

    # Section 2: Priority breakdown
    ax.text(6.2, 3.25, '2. Priority Factor Calculation:', fontsize=8.5, fontweight='bold', color='#334155')
    ax.text(6.2, 3.0, 'Sev: 0.35(80) + Saf: 0.25(100) + Aff: 0.20(60) + ... = 78.5', fontsize=7.5, color='#475569')

    # Section 3: Safety Override
    rect_ov = patches.FancyBboxPatch((6.2, 2.1), 4.0, 0.65, boxstyle='round,pad=0.05', facecolor='#FEF2F2', edgecolor='#FCA5A5')
    ax.add_patch(rect_ov)
    ax.text(6.35, 2.55, 'SAFETY OVERRIDE TRIGGERED', fontsize=8, fontweight='bold', color='#991B1B')
    ax.text(6.35, 2.25, 'Pattern: "sparking" -> Forced CRITICAL (4h SLA)', fontsize=7.5, color='#B91C1C')

    # Section 4: Human Override & Audit
    ax.text(6.2, 1.8, '3. Immutable Audit Trail:', fontsize=8.5, fontweight='bold', color='#334155')
    rect_aud = patches.Rectangle((6.2, 0.75), 4.0, 0.9, facecolor='#F1F5F9', edgecolor='#CBD5E1')
    ax.add_patch(rect_aud)
    ax.text(6.3, 1.45, '2026-10-31 10:15 | User: staff1', fontsize=7.5, fontweight='bold', color='#1E293B')
    ax.text(6.3, 1.25, 'Action: Priority Override CRITICAL -> HIGH', fontsize=7.5, color='#1E293B')
    ax.text(6.3, 1.05, 'Reason: "Switchboard power isolated; repair pending."', fontsize=7, color='#475569', fontstyle='italic')

    plt.tight_layout()
    fig.savefig('reports/figures/staff_admin_ui_flow.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    print('Generated staff_admin_ui_flow.png')

if __name__ == '__main__':
    create_student_portal_ui()
    create_staff_admin_ui()

