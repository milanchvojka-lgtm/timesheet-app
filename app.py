import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import holidays
import plotly.graph_objects as go
from io import BytesIO
import zipfile

# Page configuration
st.set_page_config(
    page_title="Timesheet Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TimesheetAnalyzer:
    def __init__(self):
        self.df = None
        self.cz_holidays = holidays.CZ()
        self.categories = {
            'Jobs': ['jobs', 'job'],
            'Reviews': ['review'],
            'Hiring': ['hiring', 'interview']
        }

    def load_data(self, df):
        self.df = df
        self.df['Datum'] = pd.to_datetime(self.df['Datum'])

    def get_working_hours_for_month(self, year, month):
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        working_days = 0
        current_day = first_day
        while current_day <= last_day:
            if current_day.weekday() < 5 and current_day not in self.cz_holidays:
                working_days += 1
            current_day += timedelta(days=1)
        return working_days * 8

    def calculate_fte(self, hours, date):
        year = date.year
        month = date.month
        monthly_hours = self.get_working_hours_for_month(year, month)
        return round(hours / monthly_hours, 2)

    def analyze_by_project(self):
        unique_months = pd.Period(self.df['Datum'].min(), freq='M')
        working_hours = self.get_working_hours_for_month(unique_months.year, unique_months.month)

        project_analysis = (
            self.df
            .groupby(['Projekt'])
            .agg({
                'Natrackováno': ['sum', 'mean', 'count']
            })
            .round(2)
        )

        project_analysis.columns = ['Celkem hodin', 'Průměr hodin', 'Počet záznamů']

        project_analysis['FTE'] = project_analysis['Celkem hodin'].apply(
            lambda x: self.calculate_fte(x, unique_months.to_timestamp())
        )

        total_hours = round(project_analysis['Celkem hodin'].sum(), 2)
        project_analysis['Podíl (%)'] = (project_analysis['Celkem hodin'] / total_hours * 100).round(2)

        total_row = pd.DataFrame({
            'Celkem hodin': [total_hours],
            'Průměr hodin': [round(project_analysis['Průměr hodin'].mean(), 2)],
            'Počet záznamů': [int(project_analysis['Počet záznamů'].sum())],
            'FTE': [round(project_analysis['FTE'].sum(), 2)],
            'Podíl (%)': [100.0]
        }, index=['CELKEM'])

        project_analysis = pd.concat([project_analysis, total_row])
        project_analysis = project_analysis.round(2)
        project_analysis['Počet záznamů'] = project_analysis['Počet záznamů'].astype(int)
        return project_analysis, working_hours, unique_months

    def _get_ops_project(self):
        ops_projects = [proj for proj in self.df['Projekt'].unique()
                       if 'ops' in proj.lower() and 'design' in proj.lower()]
        if not ops_projects:
            raise ValueError("Nenalezen žádný OPS projekt v datech")
        return ops_projects[0]

    def analyze_ops_activities(self):
        ops_project = self._get_ops_project()
        ops_data = self.df[self.df['Projekt'] == ops_project].copy()

        def categorize_description(desc):
            if pd.isna(desc):
                return 'Nespárované'
            desc = str(desc).lower()
            for category, keywords in self.categories.items():
                if any(keyword in desc for keyword in keywords):
                    return category
            return 'Nespárované'

        ops_data['Kategorie'] = ops_data['Popis'].apply(categorize_description)

        category_analysis = ops_data.groupby('Kategorie').agg({
            'Natrackováno': 'sum'
        }).round(2)

        total_hours = round(category_analysis['Natrackováno'].sum(), 2)
        category_analysis['Podíl (%)'] = (category_analysis['Natrackováno'] / total_hours * 100).round(2)

        total_row = pd.DataFrame({
            'Natrackováno': [total_hours],
            'Podíl (%)': [100.0]
        }, index=['CELKEM'])

        category_analysis = pd.concat([category_analysis, total_row])
        category_analysis = category_analysis.round(2)
        return category_analysis

    def analyze_ops_by_person(self):
        ops_project = self._get_ops_project()
        ops_data = self.df[self.df['Projekt'] == ops_project].copy()

        def categorize_description(desc):
            if pd.isna(desc):
                return 'Nespárované'
            desc = str(desc).lower()
            for category, keywords in self.categories.items():
                if any(keyword in desc for keyword in keywords):
                    return category
            return 'Nespárované'

        ops_data['Kategorie'] = ops_data['Popis'].apply(categorize_description)

        person_category_analysis = ops_data.pivot_table(
            values='Natrackováno',
            index='Osoba',
            columns='Kategorie',
            aggfunc='sum',
            fill_value=0
        ).round(2)

        person_category_analysis['Celkem'] = person_category_analysis.sum(axis=1).round(2)
        total_hours = round(person_category_analysis['Celkem'].sum(), 2)
        person_category_analysis['Podíl (%)'] = (person_category_analysis['Celkem'] / total_hours * 100).round(2)

        person_category_analysis = person_category_analysis.round(2)
        return person_category_analysis

    def get_person_fte(self):
        unique_months = pd.Period(self.df['Datum'].min(), freq='M')
        person_fte = self.df.groupby('Osoba')['Natrackováno'].sum().apply(
            lambda x: self.calculate_fte(x, unique_months.to_timestamp())
        ).sort_values()
        return person_fte


def create_bar_chart(x_data, y_data, title, xaxis_title, text_data, main_color='#FF7CAC'):
    max_value = max(x_data)
    fig = go.Figure(data=[go.Bar(
        x=x_data,
        y=y_data,
        orientation='h',
        marker_color=main_color,
        text=text_data,
        textposition='outside',
        textfont=dict(color='#333333', size=12)
    )])
    fig.update_layout(
        title=dict(text=title, font=dict(color='#333333', size=18)),
        xaxis_title=xaxis_title,
        xaxis=dict(
            range=[0, max_value * 1.4],
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='lightgrey',
            zerolinewidth=1,
            title=dict(font=dict(color='#333333', size=14)),
            tickfont=dict(color='#333333', size=12)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            tickfont=dict(color='#333333', size=12)
        ),
        margin=dict(l=250, r=500),
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        hoverlabel=dict(bgcolor='white'),
        width=1200,
        height=400,
        font=dict(color='#333333')
    )
    return fig


def create_comparison_chart(planned_data, actual_data, labels, main_color='#FF7CAC', light_color='#FFD9E5'):
    max_value = max(max(planned_data), max(actual_data))

    fig = go.Figure(data=[
        go.Bar(
            name='Plánovaný FTE',
            x=planned_data,
            y=labels,
            orientation='h',
            marker_color=light_color,
            text=[f"{x:.2f} FTE" for x in planned_data],
            textposition='outside',
            textfont=dict(color='#333333', size=12)
        ),
        go.Bar(
            name='Skutečný FTE',
            x=actual_data,
            y=labels,
            orientation='h',
            marker_color=main_color,
            text=[f"{x:.2f} FTE" for x in actual_data],
            textposition='outside',
            textfont=dict(color='#333333', size=12)
        )
    ])
    fig.update_layout(
        title=dict(text='Porovnání plánovaného a skutečného FTE', font=dict(color='#333333', size=18)),
        xaxis_title='FTE',
        xaxis=dict(
            range=[0, max_value * 1.4],
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='lightgrey',
            zerolinewidth=1,
            title=dict(font=dict(color='#333333', size=14)),
            tickfont=dict(color='#333333', size=12)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            tickfont=dict(color='#333333', size=12)
        ),
        barmode='group',
        margin=dict(l=250, r=500),
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        hoverlabel=dict(bgcolor='white'),
        width=1200,
        height=400,
        font=dict(color='#333333'),
        legend=dict(font=dict(color='#333333', size=12))
    )
    return fig


def export_to_excel(analyzer, person_fte, ops_activities, ops_by_person):
    output = BytesIO()
    project_data, _, _ = analyzer.analyze_by_project()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        project_data.to_excel(writer, sheet_name='Projekty')

        person_fte_df = pd.DataFrame({
            'Osoba': person_fte.index,
            'FTE': person_fte.values
        })
        person_fte_df.loc[len(person_fte_df)] = ['CELKEM', round(person_fte.sum(), 2)]
        person_fte_df['FTE'] = person_fte_df['FTE'].round(2)
        person_fte_df.to_excel(writer, sheet_name='FTE podle osob', index=False)

        ops_activities.to_excel(writer, sheet_name='OPS aktivity')
        ops_by_person.to_excel(writer, sheet_name='OPS aktivity podle osob')

    output.seek(0)
    return output


def export_all_charts_as_zip(figures_dict):
    """Export all plotly figures as PNG images in a ZIP file"""
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, fig in figures_dict.items():
            # Convert figure to PNG image
            img_bytes = fig.to_image(format='png', width=1200, height=600)
            # Add to ZIP file
            zip_file.writestr(f"{filename}.png", img_bytes)

    zip_buffer.seek(0)
    return zip_buffer


# Streamlit App
def main():
    # Custom CSS to prevent text wrapping in tables
    st.markdown("""
        <style>
        /* Prevent text wrapping in table cells */
        table td, table th {
            white-space: nowrap !important;
            overflow: visible !important;
            text-overflow: clip !important;
        }
        /* Remove horizontal scrollbar and allow table to expand */
        .stTable {
            overflow-x: visible !important;
        }
        [data-testid="stTable"] {
            overflow-x: visible !important;
        }
        [data-testid="stTable"] > div {
            overflow-x: visible !important;
        }
        /* Allow table to be wider than container */
        table {
            width: auto !important;
            max-width: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📊 Timesheet Analyzer")
    st.markdown("Analýza pracovních výkazů Design týmu")

    # Sidebar for file upload and settings
    st.sidebar.header("⚙️ Nastavení")

    uploaded_file = st.sidebar.file_uploader(
        "Nahrajte Excel soubor s timesheety",
        type=['xlsx'],
        help="Nahrajte export z Costlocker"
    )

    if uploaded_file is not None:
        try:
            # Load data
            df = pd.read_excel(uploaded_file)

            # Initialize analyzer
            analyzer = TimesheetAnalyzer()
            analyzer.load_data(df)

            # Get person FTE for sidebar inputs
            person_fte = analyzer.get_person_fte()

            # Sidebar - Planned FTE inputs
            st.sidebar.header("🎯 Plánované FTE")
            st.sidebar.markdown("Upravte plánované FTE pro jednotlivé osoby:")

            planned_fte = {}
            for person in person_fte.index:
                default_value = 1.0
                if 'Chvojka' in person:
                    default_value = 0.9
                elif 'Martínek' in person:
                    default_value = 0.5
                elif 'Panáková' in person:
                    default_value = 0.5
                elif 'Brza' in person:
                    default_value = 1.0
                elif 'Vybíral' in person:
                    default_value = 0.05
                elif 'Štigler' in person:
                    default_value = 0.05

                planned_fte[person] = st.sidebar.number_input(
                    person,
                    min_value=0.0,
                    max_value=1.0,
                    value=default_value,
                    step=0.05,
                    key=f"fte_{person}"
                )

            # Main content
            project_data, working_hours, unique_months = analyzer.analyze_by_project()

            # Dictionary to store all figures for batch export
            all_figures = {}

            # Info box
            st.info(f"📅 Období: {unique_months} | 💼 Pracovní hodiny: {working_hours}h = 1 FTE")

            # Project Analysis
            st.header("📈 Přehled podle projektů")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Tabulka projektů")
                # Format all numeric columns to 2 decimal places
                project_data_display = project_data.copy()
                for col in project_data_display.columns:
                    if project_data_display[col].dtype in ['float64', 'float32']:
                        project_data_display[col] = project_data_display[col].apply(lambda x: f"{x:.2f}")
                st.table(project_data_display)

            with col2:
                st.subheader("Celkové FTE")
                total_fte = project_data.loc['CELKEM', 'FTE']
                st.metric("Celkem FTE", f"{total_fte:.2f}")

            # Visualization: FTE by project
            st.subheader("FTE a podíl času podle projektů")
            project_data_sorted = project_data[:-1].sort_values('FTE')
            fig_fte = create_bar_chart(
                project_data_sorted['FTE'],
                project_data_sorted.index,
                'FTE a podíl času podle projektů',
                'FTE',
                [f"{fte:.2f} FTE ({pct:.2f}%)" for fte, pct in
                 zip(project_data_sorted['FTE'], project_data_sorted['Podíl (%)'])]
            )
            all_figures['01_FTE_podle_projektu'] = fig_fte
            st.plotly_chart(fig_fte, use_container_width=True)

            # Visualization: Hours by project
            st.subheader("Rozdělení práce mezi projekty")
            projects_sorted = project_data[:-1].sort_values('Celkem hodin', ascending=True)
            fig_hours = create_bar_chart(
                projects_sorted['Celkem hodin'],
                projects_sorted.index,
                'Rozdělení práce mezi projekty',
                'Počet hodin',
                [f"{hours:.2f}h ({pct:.2f}%)" for hours, pct in
                 zip(projects_sorted['Celkem hodin'], projects_sorted['Podíl (%)'])]
            )
            all_figures['02_Hodiny_podle_projektu'] = fig_hours
            st.plotly_chart(fig_hours, use_container_width=True)

            # Person FTE Analysis
            st.header("👥 Analýza podle osob")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("FTE podle osob")
                person_fte_df = pd.DataFrame({
                    'Osoba': person_fte.index,
                    'FTE': person_fte.values
                })
                # Format FTE to 2 decimal places
                person_fte_df['FTE'] = person_fte_df['FTE'].apply(lambda x: f"{x:.2f}")
                st.table(person_fte_df)

            with col2:
                st.subheader("Celkový přehled")
                st.metric("Celkem FTE všech osob", f"{person_fte.sum():.2f}")

            # Visualization: FTE by person
            fig_person = create_bar_chart(
                person_fte.values,
                person_fte.index,
                'FTE podle osob',
                'FTE',
                [f"{x:.2f} FTE" for x in person_fte.values]
            )
            all_figures['03_FTE_podle_osob'] = fig_person
            st.plotly_chart(fig_person, use_container_width=True)

            # Comparison: Planned vs Actual FTE
            st.subheader("Porovnání plánovaného a skutečného FTE")
            planned_fte_filtered = {person: fte for person, fte in planned_fte.items()
                                   if person in person_fte.index}
            actual_fte = person_fte[list(planned_fte_filtered.keys())]

            fig_comparison = create_comparison_chart(
                list(planned_fte_filtered.values()),
                actual_fte.values,
                list(planned_fte_filtered.keys())
            )
            all_figures['04_Porovnani_planovane_vs_skutecne_FTE'] = fig_comparison
            st.plotly_chart(fig_comparison, use_container_width=True)

            # OPS Analysis
            st.header("🔧 Analýza OPS aktivit")

            try:
                ops_activities = analyzer.analyze_ops_activities()
                ops_by_person = analyzer.analyze_ops_by_person()

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("OPS aktivity celkem")
                    # Format all numeric columns to 2 decimal places
                    ops_activities_display = ops_activities.copy()
                    for col in ops_activities_display.columns:
                        if ops_activities_display[col].dtype in ['float64', 'float32']:
                            ops_activities_display[col] = ops_activities_display[col].apply(lambda x: f"{x:.2f}")
                    st.table(ops_activities_display)

                with col2:
                    st.subheader("OPS aktivity podle osob")
                    # Format all numeric columns to 2 decimal places
                    ops_by_person_display = ops_by_person.copy()
                    for col in ops_by_person_display.columns:
                        if ops_by_person_display[col].dtype in ['float64', 'float32']:
                            ops_by_person_display[col] = ops_by_person_display[col].apply(lambda x: f"{x:.2f}")
                    st.table(ops_by_person_display)

                # Visualization: OPS activities
                ops_activities_order = ['Jobs', 'Reviews', 'Hiring', 'Nespárované']
                ops_data_reordered = ops_activities.reindex(ops_activities_order)

                fig_ops = create_bar_chart(
                    ops_data_reordered['Natrackováno'][:-1],
                    ops_data_reordered.index[:-1],
                    'Rozdělení OPS aktivit',
                    'Hodiny',
                    [f"{ops_data_reordered['Natrackováno'][i]:.2f}h ({ops_data_reordered['Podíl (%)'][i]:.2f}%)"
                     for i in ops_data_reordered.index[:-1]]
                )
                all_figures['05_OPS_aktivity_celkem'] = fig_ops
                st.plotly_chart(fig_ops, use_container_width=True)

                # Individual OPS charts per person
                st.subheader("OPS aktivity podle jednotlivých osob")

                chart_counter = 6
                for person in ops_by_person.index:
                    person_data = pd.Series(0.0, index=ops_activities_order)
                    for activity in ops_activities_order:
                        if activity in ops_by_person.columns:
                            person_data[activity] = ops_by_person.loc[person, activity]

                    fig_person_ops = create_bar_chart(
                        person_data.values,
                        person_data.index,
                        f'OPS aktivity - {person}',
                        'Hodiny',
                        [f"{val:.2f}h" for val in person_data.values]
                    )
                    all_figures[f'{chart_counter:02d}_OPS_aktivity_{person.replace(" ", "_")}'] = fig_person_ops
                    chart_counter += 1
                    st.plotly_chart(fig_person_ops, use_container_width=True)

                # Detailed view of "Nespárované" category
                st.subheader("🔍 Detail kategorie 'Nespárované'")

                ops_project = analyzer._get_ops_project()
                ops_data = analyzer.df[analyzer.df['Projekt'] == ops_project].copy()

                def categorize_description(desc):
                    if pd.isna(desc):
                        return 'Nespárované'
                    desc = str(desc).lower()
                    for category, keywords in analyzer.categories.items():
                        if any(keyword in desc for keyword in keywords):
                            return category
                    return 'Nespárované'

                ops_data['Kategorie'] = ops_data['Popis'].apply(categorize_description)
                ostatni_data = ops_data[ops_data['Kategorie'] == 'Nespárované'].copy()

                if len(ostatni_data) > 0:
                    st.markdown(f"**Počet záznamů v kategorii 'Nespárované': {len(ostatni_data)}**")
                    st.markdown(f"**Celkem hodin: {ostatni_data['Natrackováno'].sum():.2f}h**")

                    # Display detailed table
                    ostatni_display = ostatni_data[['Datum', 'Osoba', 'Natrackováno', 'Popis']].copy()
                    ostatni_display = ostatni_display.sort_values('Datum', ascending=False)
                    ostatni_display['Datum'] = ostatni_display['Datum'].dt.strftime('%Y-%m-%d')
                    ostatni_display['Natrackováno'] = ostatni_display['Natrackováno'].apply(lambda x: f"{x:.2f}")

                    st.table(ostatni_display)
                else:
                    st.success("✅ Vše natrackováno správně")

            except ValueError as e:
                st.warning(f"⚠️ {str(e)}")

            # Export buttons
            st.header("📥 Export dat")

            col1, col2 = st.columns(2)

            with col1:
                try:
                    excel_data = export_to_excel(analyzer, person_fte, ops_activities, ops_by_person)
                    st.download_button(
                        label="📥 Stáhnout Excel report",
                        data=excel_data,
                        file_name=f"timesheet_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except:
                    st.error("Nepodařilo se vytvořit Excel export")

            with col2:
                try:
                    if all_figures:
                        zip_data = export_all_charts_as_zip(all_figures)
                        st.download_button(
                            label="📊 Stáhnout všechny grafy (ZIP)",
                            data=zip_data,
                            file_name=f"timesheet_charts_{datetime.now().strftime('%Y%m%d')}.zip",
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"Nepodařilo se vytvořit export grafů: {str(e)}")

        except Exception as e:
            st.error(f"❌ Chyba při zpracování souboru: {str(e)}")
            st.info("💡 Zkontrolujte, zda soubor obsahuje správné sloupce: Datum, Projekt, Osoba, Natrackováno, Popis")

    else:
        st.info("👆 Nahrajte Excel soubor v postranním panelu pro začátek analýzy")

        # Show example format
        st.markdown("### 📋 Očekávaný formát dat")
        st.markdown("""
        Excel soubor by měl obsahovat následující sloupce:
        - **Datum** - Datum záznamu
        - **Projekt** - Název projektu
        - **Osoba** - Jméno osoby
        - **Natrackováno** - Počet hodin
        - **Popis** - Popis aktivity
        """)


if __name__ == "__main__":
    main()
