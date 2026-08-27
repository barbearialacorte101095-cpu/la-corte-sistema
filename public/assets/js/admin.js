// Painel administrativo: resumo financeiro do dia, agenda e lançamentos.

function formatarPreco(valor) {
  return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function hojeISO() {
  return new Date().toISOString().split("T")[0];
}

const statusLabel = {
  pendente: "Pendente",
  confirmado: "Confirmado",
  concluido: "Concluído",
  cancelado: "Cancelado",
  nao_compareceu: "Não compareceu",
};

// 1. CARREGA O RESUMO FINANCEIRO E ATUALIZA OS CARDS
async function carregarResumo() {
  const hoje = hojeISO();
  try {
    // Usa o helper 'api' criado pelo Claude
    const resumo = await api.get(`/financeiro/resumo?data_inicio=${hoje}&data_fim=${hoje}`);
    
    // Atualiza Faturamento
    const faturamentoEl = document.getElementById("valor-faturamento");
    if (faturamentoEl) {
        faturamentoEl.textContent = formatarPreco(resumo.entradas);
        faturamentoEl.classList.remove("text-gray-500");
        faturamentoEl.classList.add("text-white");
    }

    // Atualiza Comissões
    const comissoesEl = document.getElementById("valor-comissoes");
    if (comissoesEl) {
        comissoesEl.textContent = formatarPreco(resumo.comissoes_pendentes);
        comissoesEl.classList.remove("text-gray-500");
        comissoesEl.classList.add("text-white");
    }

  } catch (e) {
    console.error("Erro ao carregar resumo financeiro:", e);
    const faturamentoEl = document.getElementById("valor-faturamento");
    if (faturamentoEl) faturamentoEl.textContent = "Erro de conexão";
    
    const comissoesEl = document.getElementById("valor-comissoes");
    if (comissoesEl) comissoesEl.textContent = "Erro de conexão";
  }
}

// 2. CARREGA A AGENDA DO DIA E CONTA OS CORTES REALIZADOS
async function carregarAgendaDoDia() {
  const lista = document.getElementById("lista-agenda");
  
  try {
    const agendamentos = await api.get(`/agendamentos?data=${hojeISO()}`);

    // Atualiza o card de "Cortes Realizados" no painel
    const qtdCortesEl = document.getElementById('qtd-cortes');
    const qtdAgendadosEl = document.getElementById('qtd-agendados');
    
    if (qtdCortesEl && qtdAgendadosEl) {
        // Conta apenas os serviços marcados como "concluido"
        const concluidos = agendamentos.filter(a => a.status === 'concluido').length;
        qtdCortesEl.textContent = concluidos;
        qtdCortesEl.classList.remove("text-gray-500");
        qtdCortesEl.classList.add("text-white");
        
        qtdAgendadosEl.textContent = `Agendados: ${agendamentos.length}`;
    }

    if (!lista) return; // Se a tabela de agenda não estiver na tela, para por aqui

    if (agendamentos.length === 0) {
      lista.innerHTML = `<p class="text-sm text-[var(--silver-dim)] py-6 text-center">Nenhum agendamento para hoje.</p>`;
      return;
    }

    lista.innerHTML = agendamentos
      .map((a) => {
        const hora = new Date(a.data_hora_inicio).toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        });
        return `
        <div class="flex items-center justify-between py-3 border-b border-[var(--panel-border)] last:border-0">
          <div class="flex items-center gap-4">
            <span class="mono text-[var(--moss-300)] text-sm w-14">${hora}</span>
            <div>
              <p class="text-white text-sm font-medium">${a.cliente_nome}</p>
              <p class="text-xs text-[var(--silver-dim)]">${a.servico_nome} · ${a.barbeiro_nome}</p>
            </div>
          </div>
          <span class="pill pill-${a.status}">${statusLabel[a.status] ?? a.status}</span>
        </div>`;
      })
      .join("");
  } catch (e) {
    if (lista) lista.innerHTML = `<p class="text-sm text-[var(--danger-soft)] py-6 text-center">Erro ao carregar a agenda.</p>`;
  }
}

// 3. CARREGA A TABELA DE TRANSAÇÕES FINANCEIRAS
async function carregarTransacoes() {
  const tbody = document.getElementById("corpo-tabela-transacoes");
  if (!tbody) return; 
  
  try {
    const transacoes = await api.get(`/financeiro/transacoes?data_inicio=${hojeISO()}&data_fim=${hojeISO()}`);

    if (transacoes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center text-[var(--silver-dim)] py-6">Nenhum lançamento hoje.</td></tr>`;
      return;
    }

    tbody.innerHTML = transacoes
      .map(
        (t) => `
        <tr class="border-b border-[var(--panel-border)] last:border-0">
          <td class="py-3 text-sm">${t.descricao ?? t.categoria}</td>
          <td class="py-3 text-sm text-[var(--silver-dim)] capitalize">${t.categoria.replace("_", " ")}</td>
          <td class="py-3 text-sm mono ${t.tipo === "entrada" ? "text-[var(--moss-300)]" : "text-[var(--danger-soft)]"}">
            ${t.tipo === "entrada" ? "+" : "−"} ${formatarPreco(t.valor)}
          </td>
          <td class="py-3 text-xs text-[var(--silver-dim)] mono">
            ${new Date(t.data_transacao).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
          </td>
        </tr>`
      )
      .join("");
  } catch (e) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="text-center text-[var(--danger-soft)] py-6">Erro ao carregar transações.</td></tr>`;
  }
}

// 4. CADASTRA NOVA TRANSAÇÃO E ATUALIZA A TELA
document.getElementById("form-nova-transacao")?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const fd = new FormData(ev.target);
  try {
    await api.post("/financeiro/transacoes", {
      tipo: fd.get("tipo"),
      categoria: fd.get("categoria"),
      valor: parseFloat(fd.get("valor")),
      descricao: fd.get("descricao") || null,
    });
    ev.target.reset();
    document.getElementById("modal-transacao")?.classList.add("hidden");
    await Promise.all([carregarResumo(), carregarTransacoes()]);
  } catch (e) {
    alert(e.message);
  }
});

// Inicializa tudo quando a página carregar
document.addEventListener("DOMContentLoaded", () => {
  carregarResumo();
  carregarAgendaDoDia();
  carregarTransacoes();
});