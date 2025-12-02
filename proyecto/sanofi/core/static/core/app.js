document.addEventListener("DOMContentLoaded", function () {
	const listEl = document.getElementById("clientes-list");
	const refreshBtn = document.getElementById("refresh-btn");
	const form = document.getElementById("cliente-form");
	const msgEl = document.getElementById("cliente-msg");
	const nombreEl = document.getElementById("cliente-nombre");
	const nitEl = document.getElementById("cliente-nit");
	const direccionEl = document.getElementById("cliente-direccion");
	const correoEl = document.getElementById("cliente-correo");
	const telefonoEl = document.getElementById("cliente-telefono");
	const paisEl = document.getElementById("cliente-pais");
	const ciudadEl = document.getElementById("cliente-ciudad");
	const saldoEl = document.getElementById("cliente-saldo");

	async function loadClientes() {
		listEl.textContent = "Cargando clientes...";
		try {
			const res = await fetch("/api/clientes/");
			if (!res.ok) throw new Error("Error al consultar API");
			const data = await res.json();
			if (!Array.isArray(data)) {
				listEl.textContent = "Respuesta inesperada de la API";
				return;
			}
			if (data.length === 0) {
				listEl.textContent = "No hay clientes registrados.";
				return;
			}
			listEl.innerHTML = "";
			data.forEach((c) => {
				const div = document.createElement("div");
				div.className = "cliente-item";
				div.innerHTML = `
					<strong>${escapeHtml(c.nombre || c.id || "Cliente")}</strong>
					<div><b>ID:</b> ${escapeHtml(c.id)}</div>
					<div><b>NIT:</b> ${escapeHtml(c.nit ?? "")}</div>
					<div><b>Dirección:</b> ${escapeHtml(c.direccion ?? "")}</div>
					<div><b>Correo:</b> ${escapeHtml(c.correo ?? "")}</div>
					<div><b>Teléfono:</b> ${escapeHtml(c.telefono ?? "")}</div>
					<div><b>País:</b> ${escapeHtml(c.pais ?? "")}</div>
					<div><b>Ciudad:</b> ${escapeHtml(c.ciudad ?? "")}</div>
					<div><b>Saldo:</b> ${escapeHtml(c.saldo ?? "0.00")}</div>
				`;
				listEl.appendChild(div);
			});
		} catch (err) {
			listEl.textContent = "Error cargando clientes: " + err.message;
		}
	}

	function escapeHtml(unsafe) {
		return String(unsafe)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;");
	}

	refreshBtn.addEventListener("click", loadClientes);
	loadClientes();

	if (form) {
		form.addEventListener("submit", async function (e) {
			e.preventDefault();
			console.log("[cliente-form] submit triggered");
			msgEl.textContent = "";
			const nombre = (nombreEl?.value || "").trim();
			const nit = (nitEl?.value || "").trim();
			const direccion = (direccionEl?.value || "").trim();
			const correo = (correoEl?.value || "").trim();
			const telefono = (telefonoEl?.value || "").trim();
			const pais = (paisEl?.value || "").trim();
			const ciudad = (ciudadEl?.value || "").trim();
			const saldoRaw = saldoEl?.value ?? "";
			if (!nombre) {
				msgEl.textContent = "El nombre es requerido";
				return;
			}
			try {
				const headers = { "Content-Type": "application/json" };
				const csrftoken = getCsrfToken();
				if (csrftoken) headers["X-CSRFToken"] = csrftoken;
				console.log("[cliente-form] posting to /api/clientes/", {
					nombre,
					nit,
					direccion,
					correo,
					telefono,
					pais,
					ciudad,
					saldoRaw,
				});
				const res = await fetch("/api/clientes/", {
					method: "POST",
					headers,
					credentials: "same-origin",
					body: JSON.stringify({
						nombre,
						nit: nit || null,
						direccion: direccion || null,
						correo: correo || null,
						telefono: telefono || null,
						pais: pais || null,
						ciudad: ciudad || null,
						saldo: saldoRaw !== "" ? Number(saldoRaw) : null,
						archivo: null,
					}),
				});
				console.log("[cliente-form] response status", res.status);
				if (res.ok) {
					msgEl.textContent = "Cliente creado";
					form.reset();
					loadClientes();
				} else {
					const err = await res
						.json()
						.catch(() => ({ detail: "Error" }));
					msgEl.textContent =
						"Error creando cliente: " +
						(err.detail || JSON.stringify(err));
					console.error("[cliente-form] error response", err);
				}
			} catch (err) {
				msgEl.textContent = "Error creando cliente: " + err.message;
				console.error("[cliente-form] fetch failed", err);
			}
		});
	}

	function getCsrfToken() {
		// Prefer meta tag value rendered by Django
		const meta = document.querySelector('meta[name="csrf-token"]');
		if (meta && meta.content) return meta.content;
		// Fallback to cookie if available
		const value = `; ${document.cookie}`;
		const parts = value.split(`; csrftoken=`);
		if (parts.length === 2) return parts.pop().split(";").shift();
		return null;
	}
});
