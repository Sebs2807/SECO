document.addEventListener("DOMContentLoaded", function () {
	const confMsg = document.getElementById("conf-msg");
	const chartMsg = document.getElementById("chart-msg");
	const resetBtn = document.getElementById("reset-btn");
	const form = document.getElementById("bucket-form");
	const ctx = document.getElementById("estadoChart");

	const inputs = {
		b1_start: document.getElementById("b1_start"),
		b1_end: document.getElementById("b1_end"),
		b2_start: document.getElementById("b2_start"),
		b2_end: document.getElementById("b2_end"),
		b3_start: document.getElementById("b3_start"),
		b3_end: document.getElementById("b3_end"),
	};

	let chart;

	function getParams() {
		return {
			b1_start: parseInt(inputs.b1_start.value) || 0,
			b1_end: parseInt(inputs.b1_end.value) || 60,
			b2_start: parseInt(inputs.b2_start.value) || 60,
			b2_end: parseInt(inputs.b2_end.value) || 120,
			b3_start: parseInt(inputs.b3_start.value) || 120,
			b3_end: parseInt(inputs.b3_end.value) || 180,
		};
	}

	function buildQuery(params) {
		const usp = new URLSearchParams(params);
		return "/api/facturas/aging_buckets/?" + usp.toString();
	}

	async function loadData() {
		chartMsg.textContent = "Cargando datos...";
		try {
			const res = await fetch(buildQuery(getParams()));
			if (!res.ok) throw new Error("Error al consultar API");
			const data = await res.json();
			renderChart(data);
			chartMsg.textContent = data.length
				? ""
				: "No hay facturas abiertas en los rangos configurados.";
		} catch (err) {
			chartMsg.textContent = "Error cargando datos: " + err.message;
		}
	}

	function renderChart(rows) {
		// Aggregate totals across all clients for the three buckets
		const total_en_tiempo = rows.reduce(
			(acc, r) => acc + (r.en_tiempo || 0),
			0
		);
		const total_pendiente = rows.reduce(
			(acc, r) => acc + (r.pendiente || 0),
			0
		);
		const total_en_riesgo = rows.reduce(
			(acc, r) => acc + (r.en_riesgo || 0),
			0
		);

		const data = {
			labels: ["En tiempo", "Pendiente", "En riesgo"],
			datasets: [
				{
					label: "Cantidad",
					data: [total_en_tiempo, total_pendiente, total_en_riesgo],
					backgroundColor: ["#4caf50", "#ff9800", "#f44336"],
				},
			],
		};

		const options = {
			responsive: true,
			plugins: {
				legend: { display: false },
				title: { display: true, text: "Facturas abiertas por estado" },
			},
			scales: {
				x: { stacked: false },
				y: {
					stacked: false,
					beginAtZero: true,
					ticks: { precision: 0 },
				},
			},
		};

		if (chart) chart.destroy();
		chart = new Chart(ctx, { type: "bar", data, options });
	}

	form.addEventListener("submit", function (e) {
		e.preventDefault();
		confMsg.textContent = "Actualizando...";
		loadData().then(() => (confMsg.textContent = "Rangos aplicados"));
	});

	resetBtn.addEventListener("click", function () {
		inputs.b1_start.value = 0;
		inputs.b1_end.value = 60;
		inputs.b2_start.value = 60;
		inputs.b2_end.value = 120;
		inputs.b3_start.value = 120;
		inputs.b3_end.value = 180;
		confMsg.textContent = "Reset a valores por defecto";
		loadData();
	});

	// init
	loadData();
});
