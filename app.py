# ==========================================
# MÓDULO: GESTIÓN DE LEADS
# ==========================================
elif opcion == "Gestión de Leads (Mail/WhatsApp)":
    st.title("📥 Gestión y Calificación de Leads")

    df_leads, ws_leads = cargar_tabla("Leads")

    if df_leads.empty:
        st.info("No hay leads registrados aún.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Leads", len(df_leads))
        col2.metric("Nuevos", len(df_leads[df_leads["Estado"] == "Nuevo"]))
        col3.metric("Contactados", len(df_leads[df_leads["Estado"] == "Contactado"]))

        st.divider()

        filtro = st.selectbox("Filtrar por estado:", ["Todos", "Nuevo", "Contactado", "Ganado", "Perdido"])
        df_mostrar = df_leads if filtro == "Todos" else df_leads[df_leads["Estado"] == filtro]

        for index, row in df_mostrar.iterrows():
            with st.expander(f"🔴 {row['Estado']} | {row['Asunto']} - {row['Remitente']}"):
                st.write(f"**Fecha:** {row['Fecha']}")
                st.write(f"**Teléfono:** {row['Telefono']}")
                st.caption(f"**Mensaje:** {row['Mensaje']}")
                
                # Botón de WhatsApp directo
                if row['Telefono'] != "No detectado":
                    tel_limpio = re.sub(r'\D', '', str(row['Telefono']))
                    wa_url = f"https://wa.me/{tel_limpio}?text=Hola,%20recibimos%20tu%20consulta"
                    st.markdown(f"[💬 Contactar por WhatsApp]({wa_url})", unsafe_allow_html=True)
