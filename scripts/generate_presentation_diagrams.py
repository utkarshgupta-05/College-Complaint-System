import os
import matplotlib
os.environ['MPLCONFIGDIR'] = os.path.abspath('reports/figures')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')

    # Color definitions
    primary_blue = '#1E3A8A'
    accent_blue = '#2563EB'
    light_blue = '#EFF6FF'
    border_blue = '#93C5FD'
    
    teal = '#0D9488'
    light_teal = '#F0FDFA'
    border_teal = '#99F6E4'
    
    amber = '#D97706'
    light_amber = '#FFFBEB'
    border_amber = '#FDE68A'
    
    purple = '#7C3AED'
    light_purple = '#F5F3FF'
    border_purple = '#DDD6FE'

    # Title
    ax.text(6, 6.6, 'End-to-End System Architecture', ha='center', va='center', 
            fontsize=18, fontweight='bold', color='#0F172A')
    ax.text(6, 6.25, 'Decoupled 3-Tier Enterprise Service Platform', ha='center', va='center', 
            fontsize=11, color='#64748B')

    # Box Helper
    def draw_tier(x, y, w, h, bg, border, title, title_color):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                                      facecolor=bg, edgecolor=border, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.25, title, ha='center', va='center', 
                fontsize=11, fontweight='bold', color=title_color)

    def draw_card(x, y, w, h, bg, border, title, desc, title_color='#0F172A'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.1",
                                      facecolor=bg, edgecolor=border, linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + 0.12, title, ha='center', va='center', 
                fontsize=9.5, fontweight='bold', color=title_color)
        ax.text(x + w/2, y + h/2 - 0.18, desc, ha='center', va='center', 
                fontsize=7.5, color='#475569', multialignment='center')

    # 1. Presentation Tier (Top)
    draw_tier(0.5, 4.4, 11, 1.5, light_blue, border_blue, '1. Presentation Tier (React 18 + Vite SPA)', primary_blue)
    draw_card(0.8, 4.55, 3.2, 0.95, '#FFFFFF', '#BFDBFE', 'Student Portal', 'Real-Time Keystroke Triage\nAdvisory Duplicate Alerts')
    draw_card(4.4, 4.55, 3.2, 0.95, '#FFFFFF', '#BFDBFE', 'Staff Portal', 'Departmental Queues & Review\nExplainability Detail Modal')
    draw_card(8.0, 4.55, 3.2, 0.95, '#FFFFFF', '#BFDBFE', 'Admin Dashboard', 'Campus KPIs & Hotspots\nDBSCAN Cluster Analysis')

    # 2. Application Tier (Middle-Left)
    draw_tier(0.5, 2.3, 4.2, 1.7, light_teal, border_teal, '2. API Gateway (FastAPI Async)', teal)
    draw_card(0.8, 3.05, 3.6, 0.65, '#FFFFFF', '#A7F3D0', '/api/complaints', 'CRUD & Real-Time /analyze')
    draw_card(0.8, 2.40, 1.75, 0.55, '#FFFFFF', '#A7F3D0', '/api/auth', 'JWT & RBAC')
    draw_card(2.65, 2.40, 1.75, 0.55, '#FFFFFF', '#A7F3D0', '/api/analytics', 'Hotspots & KPIs')

    # 3. AI / ML Inference Tier (Middle-Right)
    draw_tier(5.0, 2.3, 6.5, 1.7, light_purple, border_purple, '3. AI / ML Inference Services (Singleton Memory)', purple)
    draw_card(5.2, 3.05, 2.9, 0.65, '#FFFFFF', '#C4B5FD', 'E2 Calibrated Linear SVM', '11 Classes | Acc: 98.90% | 0.11 ms')
    draw_card(8.3, 3.05, 3.0, 0.65, '#FFFFFF', '#C4B5FD', 'E6 TF-IDF Duplicate Retriever', 'Sparse Cosine Sim | Hit@3: 100%')
    draw_card(5.2, 2.40, 2.9, 0.55, '#FFFFFF', '#C4B5FD', 'Multi-Factor Priority Engine', 'P_base (5-100) + 55 Safety Overrides')
    draw_card(8.3, 2.40, 3.0, 0.55, '#FFFFFF', '#C4B5FD', 'E10 Hotspot Discovery', 'DBSCAN Cosine Clustering (eps=0.58)')

    # 4. Data & Persistence Tier (Bottom)
    draw_tier(0.5, 0.3, 11, 1.6, light_amber, border_amber, '4. Persistence & Governance Tier', amber)
    draw_card(0.8, 0.45, 3.3, 1.1, '#FFFFFF', '#FDE68A', 'Relational Database', 'PostgreSQL 15+ (Production Pool)\nSQLite (Automated Testing CI)')
    draw_card(4.4, 0.45, 3.3, 1.1, '#FFFFFF', '#FDE68A', 'Alembic Migrations', 'Version-Controlled Schema\nTransactional Safe Upgrades')
    draw_card(8.0, 0.45, 3.2, 1.1, '#FFFFFF', '#FDE68A', 'Immutable Audit Logs', 'Priority Override History\nFull Human Accountability')

    # Connection Arrows
    def arrow(x1, y1, x2, y2, color='#64748B'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.5, shrinkA=3, shrinkB=3))

    arrow(2.4, 4.4, 2.4, 4.0, accent_blue)
    arrow(2.6, 4.0, 2.6, 4.4, accent_blue)
    arrow(6.0, 4.4, 4.2, 4.0, accent_blue)
    arrow(9.6, 4.4, 4.5, 4.0, accent_blue)

    arrow(4.7, 3.1, 5.0, 3.1, purple)
    arrow(5.0, 2.8, 4.7, 2.8, purple)

    arrow(2.6, 2.3, 2.6, 1.9, amber)
    arrow(8.0, 2.3, 8.0, 1.9, amber)

    plt.tight_layout()
    fig.savefig('reports/figures/system_architecture_diagram.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    print('Generated reports/figures/system_architecture_diagram.png')

def create_ai_pipeline_diagram():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.5)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')

    # Title
    ax.text(6, 6.15, 'Multi-Stage Intelligent AI Triage Pipeline', ha='center', va='center', 
            fontsize=17, fontweight='bold', color='#0F172A')
    ax.text(6, 5.8, 'Parallel NLP Categorization, Duplicate Retrieval & Safety Prioritization', ha='center', va='center', 
            fontsize=10.5, color='#64748B')

    def draw_box(x, y, w, h, bg, border, title, desc, title_color='#0F172A', rad=0.1):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.08,rounding_size={rad}",
                                      facecolor=bg, edgecolor=border, linewidth=1.3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + 0.12, title, ha='center', va='center', 
                fontsize=9.5, fontweight='bold', color=title_color)
        ax.text(x + w/2, y + h/2 - 0.18, desc, ha='center', va='center', 
                fontsize=7.5, color='#475569', multialignment='center')

    # Input Node
    draw_box(0.4, 2.3, 1.8, 1.2, '#EFF6FF', '#3B82F6', 'Input Text', 'Student Grievance\n(Free Natural Language)', '#1E40AF')

    # Pipeline A: Classification
    draw_box(2.7, 3.8, 2.0, 1.1, '#F0FDFA', '#14B8A6', 'Preprocessing', 'Lower, Lemmatize\nStopwords Filtering', '#0F766E')
    draw_box(5.1, 3.8, 2.2, 1.1, '#F0FDFA', '#14B8A6', 'TF-IDF Features', 'Unigram + Bigram (1,2)\n10,000 Sparse Features', '#0F766E')
    draw_box(7.7, 3.8, 2.1, 1.1, '#F5F3FF', '#8B5CF6', 'Calibrated SVM', 'LinearSVC + Platt Sigmoid\nPosterior Probabilities', '#6D28D9')

    # Confidence Gate
    draw_box(10.2, 4.5, 1.5, 0.9, '#ECFDF5', '#10B981', 'Auto-Route', 'Conf >= 0.60\n(98.9% Vol | 100% Acc)', '#047857')
    draw_box(10.2, 3.2, 1.5, 0.9, '#FFFBEB', '#F59E0B', 'Review Queue', 'Conf < 0.60\n(Catches 100% Errors)', '#B45309')

    # Pipeline B: Duplicate Detection
    draw_box(2.7, 2.2, 2.5, 1.1, '#EFF6FF', '#3B82F6', 'TF-IDF Index Search', 'Sparse Dot-Product Query\nLatency: 2.15 ms', '#1D4ED8')
    draw_box(5.6, 2.2, 2.5, 1.1, '#EFF6FF', '#3B82F6', 'Top-k Candidate Filter', 'Cosine Sim >= 0.50\nHit@3: 100% | MRR: 0.89', '#1D4ED8')
    draw_box(8.5, 2.2, 2.2, 1.1, '#DBEAFE', '#2563EB', 'Advisory Card', 'Link Existing Incident\nPrevent Work Duplication', '#1E40AF')

    # Pipeline C: Priority & Safety
    draw_box(2.7, 0.5, 2.5, 1.2, '#FEF2F2', '#EF4444', '55 Safety Patterns', 'Regex Hazard Scanner\n(Electrical, Fire, Ragging)', '#B91C1C')
    draw_box(5.6, 0.5, 2.5, 1.2, '#F8FAFC', '#94A3B8', 'P_base Formula', '0.35Sev + 0.25Saf + 0.20Aff\n+ 0.10Wait + 0.10Rec', '#334155')
    draw_box(8.5, 0.5, 2.2, 1.2, '#FEF2F2', '#EF4444', 'CRITICAL Override', 'Immediate Escalation\n4-Hour SLA Enforced', '#B91C1C')

    # Arrows
    def arrow(x1, y1, x2, y2, color='#64748B'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.5, shrinkA=2, shrinkB=2))

    # From Input to branches
    arrow(2.2, 3.1, 2.7, 4.3, '#0D9488')
    arrow(2.2, 2.8, 2.7, 2.8, '#2563EB')
    arrow(2.2, 2.5, 2.7, 1.1, '#DC2626')

    # Classification branch
    arrow(4.7, 4.3, 5.1, 4.3, '#0D9488')
    arrow(7.3, 4.3, 7.7, 4.3, '#0D9488')
    arrow(9.8, 4.5, 10.2, 4.9, '#10B981')
    arrow(9.8, 4.1, 10.2, 3.7, '#F59E0B')

    # Duplicate branch
    arrow(5.2, 2.7, 5.6, 2.7, '#2563EB')
    arrow(8.1, 2.7, 8.5, 2.7, '#2563EB')

    # Priority branch
    arrow(5.2, 1.1, 5.6, 1.1, '#64748B')
    arrow(8.1, 1.1, 8.5, 1.1, '#DC2626')

    plt.tight_layout()
    fig.savefig('reports/figures/ai_pipeline_flow.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    print('Generated reports/figures/ai_pipeline_flow.png')

if __name__ == '__main__':
    create_architecture_diagram()
    create_ai_pipeline_diagram()

