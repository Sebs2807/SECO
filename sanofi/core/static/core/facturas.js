document.addEventListener("DOMContentLoaded", function () {
	const clienteSelect = document.getElementById("cliente-select");
	const filterSelect = document.getElementById("filter-cliente");
	const filterResetBtn = document.getElementById("filter-reset");
	const facturasList = document.getElementById("facturas-list");
	const form = document.getElementById("factura-form");
	const msg = document.getElementById("form-msg");

	async function loadClientes() {
		clienteSelect.innerHTML = '<option value="">Cargando...</option>';
		try {
			const res = await fetch("/api/clientes/");
			if (!res.ok) throw new Error("Error al cargar clientes");
			const data = await res.json();
			clienteSelect.innerHTML =
				'<option value="">-- seleccionar cliente --</option>';
			data.forEach((c) => {
				const opt = document.createElement("option");
				opt.value = c.id;
				opt.textContent = c.nombre || `Cliente ${c.id}`;
				clienteSelect.appendChild(opt);
			});
		} catch (err) {
			clienteSelect.innerHTML =
				'<option value="">Error cargando clientes</option>';
			console.error(err);
		}
	}

	async function loadFacturas() {
		facturasList.textContent = "Cargando facturas...";
		try {
			const clienteId = (filterSelect && filterSelect.value) || "";
			const url = clienteId
				? `/api/facturas/?cliente=${encodeURIComponent(clienteId)}`
				: "/api/facturas/";
			const res = await fetch(url);
			if (!res.ok) throw new Error("Error al cargar facturas");
			const data = await res.json();

			// 🔥 FILTRAR: Solo facturas abiertas
			const abiertas = data.filter((f) => f.estado === "OPEN");

			if (!Array.isArray(abiertas) || abiertas.length === 0) {
				facturasList.textContent = "No hay facturas abiertas.";
				return;
			}

			facturasList.innerHTML = "";
			abiertas.forEach((f) => {
				const d = document.createElement("div");
				d.className = "factura-item";
				d.innerHTML = `<strong>${escapeHtml(
					f.numero_factura
				)}</strong> <span class="muted">(${escapeHtml(f.tipo)})</span>
			<div>Cliente: ${escapeHtml(f.cliente)}</div>
			<div>Monto: ${escapeHtml(f.monto)} ${escapeHtml(f.moneda)}</div>
			<div class="muted">Estado: ${escapeHtml(f.estado)}</div>`;
				facturasList.appendChild(d);
			});
		} catch (err) {
			facturasList.textContent =
				"Error cargando facturas: " + err.message;
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

	form.addEventListener("submit", async function (e) {
		e.preventDefault();
		msg.textContent = "";
		const formData = new FormData(form);
		const payload = {
			numero_factura: formData.get("numero_factura"),
			cliente: parseInt(formData.get("cliente")) || null,
			fecha_emision: formData.get("fecha_emision"),
			monto: formData.get("monto"),
			moneda: formData.get("moneda"),
			tipo: formData.get("tipo"),
		};

		if (!payload.cliente) {
			msg.textContent = "Selecciona un cliente";
			return;
		}

		try {
			const res = await fetch("/api/facturas/", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload),
			});
			if (res.status === 201 || res.status === 200) {
				msg.textContent = "Factura creada correctamente";
				form.reset();
				loadFacturas();
			} else {
				const err = await res.json().catch(() => ({ detail: "Error" }));
				msg.textContent =
					"Error creando factura: " +
					(err.detail || JSON.stringify(err));
			}
		} catch (err) {
			msg.textContent = "Error creando factura: " + err.message;
		}
	});

	async function loadClientesForFilter() {
		if (!filterSelect) return;
		filterSelect.innerHTML = '<option value="">Todos los clientes</option>';
		try {
			const res = await fetch("/api/clientes/");
			if (!res.ok) throw new Error("Error al cargar clientes");
			const data = await res.json();
			data.forEach((c) => {
				const opt = document.createElement("option");
				opt.value = c.id;
				opt.textContent = c.nombre || `Cliente ${c.id}`;
				filterSelect.appendChild(opt);
			});
		} catch (err) {
			console.error(err);
		}
	}

	if (filterSelect) {
		filterSelect.addEventListener("change", loadFacturas);
	}
	if (filterResetBtn) {
		filterResetBtn.addEventListener("click", () => {
			if (filterSelect) filterSelect.value = "";
			loadFacturas();
		});
	}

	// init
	loadClientes();
	loadClientesForFilter();
	loadFacturas();
});
