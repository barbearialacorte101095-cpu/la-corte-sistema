// Fluxo de agendamento: serviço -> barbeiro -> data/horário -> dados -> confirmação

const state = {
  passo: 1,
  servico: null,
  barbeiro: null,
  data: null,
  horario: null,
};

const els = {
  passos: document.querySelectorAll("[data-passo]"),
  trilha: document.getElementById("trilha-passos"),
  listaServicos: document.getElementById("lista-servicos"),
  listaBarbeiros: document.getElementById("lista-barbeiros"),
  inputData: document.getElementById("input-data"),
  gradeHorarios: document.getElementById("grade-horarios"),
  form: document.getElementById("form-dados-cliente"),
  resumo: document.getElementById("resumo-agendamento"),
  telaSucesso: document.getElementById("tela-sucesso"),
  erro: document.getElementById("mensagem-erro"),
};

function formatarPreco(valor) {
  return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function mostrarErro(msg) {
  els.erro.textContent = msg;
  els.erro.classList.remove("hidden");
  setTimeout(() => els.erro.classList.add("hidden"), 5000);
}

function irParaPasso(n) {
  state.passo = n;
  els.passos.forEach((el) => {
    el.classList.toggle("hidden", Number(el.dataset.passo) !== n);
  });
  els.trilha.querySelectorAll("[data-trilha]").forEach((el) => {
    const ativo = Number(el.dataset.trilha) <= n;
    el.classList.toggle("text-white", ativo);
    el.classList.toggle("text-[var(--silver-dim)]", !ativo);
  });
}

async function carregarServicos() {
  const servicos = await api.get("/servicos");
  els.listaServicos.innerHTML = servicos
    .map(
      (s) => `
      <button class="card p-5 text-left hover:border-[var(--moss-500)] transition-colors w-full"
              data-id="${s.id}" data-nome="${s.nome}" data-preco="${s.preco}"
              onclick="selecionarServico(this)">
        <div class="flex items-center justify-between">
          <h3 class="font-display text-lg text-white">${s.nome}</h3>
          <span class="mono text-[var(--moss-300)]">${formatarPreco(s.preco)}</span>
        </div>
        <p class="text-sm text-[var(--silver-dim)] mt-1">${s.descricao ?? ""}</p>
        <p class="text-xs mono text-[var(--silver-dim)] mt-3">${s.duracao_minutos} min</p>
      </button>`
    )
    .join("");
}

window.selecionarServico = function (btn) {
  state.servico = { id: btn.dataset.id, nome: btn.dataset.nome, preco: btn.dataset.preco };
  carregarBarbeiros();
  irParaPasso(2);
};

async function carregarBarbeiros() {
  const barbeiros = await api.get("/barbeiros");
  els.listaBarbeiros.innerHTML = barbeiros
    .map(
      (b) => `
      <button class="card p-5 text-left hover:border-[var(--moss-500)] transition-colors w-full"
              data-id="${b.id}" data-nome="${b.nome}" onclick="selecionarBarbeiro(this)">
        <h3 class="font-display text-lg text-white">${b.nome}</h3>
        <p class="text-xs mono text-[var(--silver-dim)] mt-1">Disponível esta semana</p>
      </button>`
    )
    .join("");
}

window.selecionarBarbeiro = function (btn) {
  state.barbeiro = { id: btn.dataset.id, nome: btn.dataset.nome };
  irParaPasso(3);
  const hoje = new Date().toISOString().split("T")[0];
  els.inputData.min = hoje;
  els.inputData.value = hoje;
  carregarHorarios();
};

async function carregarHorarios() {
  state.data = els.inputData.value;
  if (!state.data) return;

  els.gradeHorarios.innerHTML = `<p class="text-sm text-[var(--silver-dim)] col-span-full">Carregando horários…</p>`;

  try {
    const horarios = await api.get(
      `/agendamentos/disponibilidade?barbeiro_id=${state.barbeiro.id}&servico_id=${state.servico.id}&data=${state.data}`
    );

    if (horarios.length === 0) {
      els.gradeHorarios.innerHTML = `<p class="text-sm text-[var(--silver-dim)] col-span-full">Nenhum horário livre nesse dia. Tente outra data.</p>`;
      return;
    }

    els.gradeHorarios.innerHTML = horarios
      .map(
        (h) => `
        <button class="btn-ghost rounded-lg py-2 mono text-sm" data-horario="${h}" onclick="selecionarHorario(this)">
          ${h}
        </button>`
      )
      .join("");
  } catch (e) {
    mostrarErro(e.message);
  }
}

window.selecionarHorario = function (btn) {
  document.querySelectorAll("[data-horario]").forEach((el) => el.classList.remove("btn-primary"));
  btn.classList.add("btn-primary");
  state.horario = btn.dataset.horario;
  atualizarResumo();
  irParaPasso(4);
};

function atualizarResumo() {
  els.resumo.innerHTML = `
    <div class="flex justify-between py-2 border-b border-[var(--panel-border)]">
      <span class="text-[var(--silver-dim)]">Serviço</span><span>${state.servico.nome}</span>
    </div>
    <div class="flex justify-between py-2 border-b border-[var(--panel-border)]">
      <span class="text-[var(--silver-dim)]">Barbeiro</span><span>${state.barbeiro.nome}</span>
    </div>
    <div class="flex justify-between py-2 border-b border-[var(--panel-border)]">
      <span class="text-[var(--silver-dim)]">Data</span><span class="mono">${state.data} às ${state.horario}</span>
    </div>
    <div class="flex justify-between py-2">
      <span class="text-[var(--silver-dim)]">Valor</span><span class="mono text-[var(--moss-300)]">${formatarPreco(state.servico.preco)}</span>
    </div>`;
}

els.inputData?.addEventListener("change", carregarHorarios);

els.form?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const formData = new FormData(els.form);

  const dataHoraInicio = `${state.data}T${state.horario}:00`;

  try {
    await api.post("/agendamentos", {
      cliente_nome: formData.get("nome"),
      cliente_telefone: formData.get("telefone"),
      cliente_email: formData.get("email") || null,
      barbeiro_id: state.barbeiro.id,
      servico_id: state.servico.id,
      data_hora_inicio: dataHoraInicio,
      observacoes: formData.get("observacoes") || null,
    });

    els.passos.forEach((el) => el.classList.add("hidden"));
    els.telaSucesso.classList.remove("hidden");
  } catch (e) {
    mostrarErro(e.message);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  carregarServicos().catch((e) => mostrarErro(e.message));
});
