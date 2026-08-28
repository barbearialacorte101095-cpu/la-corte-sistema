// ==========================================
// 1. SISTEMA DE SEGURANÇA E UTILITÁRIOS
// ==========================================
if (!localStorage.getItem('token_lacorte')) {
    window.location.href = '/login.html';
}

window.fazerLogout = function() {
    localStorage.removeItem('token_lacorte');
    window.location.href = '/login.html';
}

function formatarPreco(valor) {
    return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function hojeISO() {
    return new Date().toISOString().split("T")[0];
}

// ==========================================
// 2. DASHBOARD E CAIXA
// ==========================================
window.abrirCaixa = async function() {
    const valorInicial = prompt("Digite o valor de troco inicial na gaveta (ex: 50.00):");
    if (valorInicial && !isNaN(valorInicial.replace(',', '.'))) {
        const valorFormatado = parseFloat(valorInicial.replace(',', '.'));
        try {
            const res = await fetch('/api/financeiro/transacoes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tipo: "entrada",
                    categoria: "outro", // A palavra exata que a API exige
                    valor: valorFormatado,
                    descricao: "Abertura de Caixa (Fundo)"
                })
            });
            
            if (!res.ok) throw new Error("A API recusou o formato.");
            
            document.getElementById("valor-caixa-abertura").textContent = formatarPreco(valorFormatado);
            document.getElementById("valor-caixa-abertura").classList.replace("text-gray-500", "text-white");
            alert("Caixa aberto com sucesso!");
        } catch (e) {
            alert("Erro ao abrir caixa: " + e.message);
        }
    }
};

// ... Mantenha as funções carregarAgendaDoDia e carregarDashboard exatamente como estão ...

async function carregarAgendaDoDia() {
    try {
        const res = await fetch(`/api/agendamentos?data=${hojeISO()}`);
        const agendamentos = await res.json();
        const tbodyFila = document.getElementById('lista-fila-agendamentos');
        
        if (tbodyFila && Array.isArray(agendamentos)) {
            if (agendamentos.length === 0) {
                tbodyFila.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-gray-500">Nenhum agendamento para hoje.</td></tr>`;
            } else {
                tbodyFila.innerHTML = agendamentos.map(a => {
                    const hora = new Date(a.data_hora_inicio).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
                    const nome = a.cliente_nome || "Cliente";
                    const tel = a.cliente_telefone || "";
                    
                    return `
                    <tr class="border-b border-gray-800 hover:bg-chumbo transition-colors">
                        <td class="p-4 font-bold text-verde-destaque text-lg">${hora}</td>
                        <td class="p-4">
                            <p class="text-white font-medium uppercase tracking-wider">${nome}</p>
                            <p class="text-xs text-gray-500">${tel}</p>
                        </td>
                        <td class="p-4 text-center">
                            <span class="text-xs px-2 py-1 rounded bg-yellow-900 text-yellow-300 uppercase tracking-widest font-bold">Pendente</span>
                        </td>
                    </tr>
                `}).join('');
            }
        }
    } catch (e) {
        console.error("Erro ao carregar fila:", e);
    }
}

async function carregarDashboard() {
    const hoje = hojeISO();
    const dataAtual = new Date();
    const primeiroDiaMes = new Date(dataAtual.getFullYear(), dataAtual.getMonth(), 1).toISOString().split('T')[0];
    const ultimoDiaMes = new Date(dataAtual.getFullYear(), dataAtual.getMonth() + 1, 0).toISOString().split('T')[0];

    let faturamentoHoje = 0;
    let concluidos = 0;
    let agendados = 0;

    // 1. Tenta carregar faturamento (independente)
    try {
        const resumoHoje = await api.get(`/financeiro/resumo?data_inicio=${hoje}&data_fim=${hoje}`);
        faturamentoHoje = resumoHoje.entradas || 0;
    } catch (e) { console.error("Aviso: Faturamento falhou", e); }

    // 2. Tenta carregar agendamentos (independente)
    try {
        const agendamentosHoje = await api.get(`/agendamentos?data=${hoje}`);
        if (Array.isArray(agendamentosHoje)) {
            concluidos = agendamentosHoje.filter(a => a.status === 'concluido').length;
            agendados = agendamentosHoje.length;
        }
    } catch (e) { console.error("Aviso: Agendamentos falharam", e); }

    const ticketMedio = concluidos > 0 ? faturamentoHoje / concluidos : 0;

    // 3. Atualiza a tela sem depender de Promise.all
    const els = {
        fatHoje: document.getElementById("valor-faturamento"),
        cortes: document.getElementById("qtd-cortes"),
        agendados: document.getElementById("qtd-agendados"),
        ticket: document.getElementById("valor-ticket")
    };

    if(els.fatHoje) {
        els.fatHoje.textContent = formatarPreco(faturamentoHoje);
        els.fatHoje.classList.replace("text-gray-500", "text-white");
        
        els.cortes.textContent = concluidos;
        els.cortes.classList.replace("text-gray-500", "text-white");
        els.agendados.textContent = `Agendados: ${agendados}`;
        
        els.ticket.textContent = formatarPreco(ticketMedio);
        els.ticket.classList.replace("text-gray-500", "text-white");
    }

    await carregarAgendaDoDia();
}

// ==========================================
// 3. ABA DE SERVIÇOS
// ==========================================
async function carregarServicos() {
    try {
        const servicos = await api.get('/servicos');
        const tbody = document.getElementById('lista-servicos-tabela');
        const selectPdv = document.getElementById('pdv-servico');
        
        if (tbody) {
            if (!servicos || servicos.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-gray-500">Nenhum serviço cadastrado.</td></tr>`;
            } else {
                tbody.innerHTML = servicos.map(s => `
                    <tr class="border-b border-gray-800 hover:bg-chumbo-claro transition-colors">
                        <td class="p-4 text-sm font-medium text-white">${s.nome}</td>
                        <td class="p-4 text-sm text-verde-destaque font-bold">R$ ${Number(s.preco).toFixed(2).replace('.', ',')}</td>
                        <td class="p-4 text-center">
                            <button onclick="excluirServico('${s.id}')" class="text-red-500 hover:text-red-400 text-xs uppercase tracking-wider">Excluir</button>
                        </td>
                    </tr>
                `).join('');
            }
        }

        if (selectPdv && servicos && servicos.length > 0) {
            selectPdv.innerHTML = '<option value="" disabled selected>Selecione um serviço...</option>' + 
                servicos.map(s => `
                    <option value="${s.preco}">${s.nome} - R$ ${Number(s.preco).toFixed(2).replace('.', ',')}</option>
                `).join('');
        }
    } catch (erro) {
        console.error("Erro ao carregar serviços:", erro);
    }
}

const formNovoServico = document.getElementById('form-novo-servico');
if (formNovoServico) {
    formNovoServico.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const btnSubmit = ev.target.querySelector('button[type="submit"]');
        const textoOriginal = btnSubmit.innerHTML;
        btnSubmit.innerHTML = 'Salvando...';

        const nome = document.getElementById('nome-servico').value;
        const preco = parseFloat(document.getElementById('preco-servico').value);

        try {
            await api.post('/servicos', { nome: nome, preco: preco, duracao_minutos: 30, descricao: "" });
            formNovoServico.reset();
            await carregarServicos(); 
            alert("Serviço cadastrado com sucesso!");
        } catch (e) {
            alert("Falha ao salvar: " + (e.message || JSON.stringify(e)));
        } finally {
            btnSubmit.innerHTML = textoOriginal;
        }
    });
}

window.excluirServico = async function(id) {
    if(confirm("Deseja excluir este serviço?")) {
        try {
            const resposta = await fetch(`/api/servicos/${id}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!resposta.ok) throw new Error(`Erro na exclusão.`);
            await carregarServicos(); 
        } catch(e) {
            alert("Falha ao excluir: " + e.message);
        }
    }
};

// ==========================================
// 4. REGISTRAR VENDA (PDV)
// ==========================================
const formPdv = document.getElementById('form-pdv');
if (formPdv) {
    formPdv.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const selectServico = document.getElementById('pdv-servico');
        const valorServico = parseFloat(selectServico.value);
        const nomeServico = selectServico.options[selectServico.selectedIndex].text.split(' - ')[0]; 
        const metodoPagamento = document.getElementById('pdv-pagamento').value;

        const btnSubmit = ev.target.querySelector('button[type="submit"]');
        const textoOriginal = btnSubmit.innerHTML;
        btnSubmit.innerHTML = 'Processando...';

        try {
            await api.post("/financeiro/transacoes", {
                tipo: "entrada",
                categoria: "servico", // A palavra exata que a API exige
                valor: valorServico,
                descricao: `${nomeServico} (Pago no ${metodoPagamento})` // Salva como foi pago na descrição
            });
            formPdv.reset();
            await carregarDashboard(); 
            alert("Venda registrada com sucesso!");
        } catch (erro) {
            alert("Erro ao registrar a venda.");
        } finally {
            btnSubmit.innerHTML = textoOriginal;
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    carregarDashboard();
    carregarServicos();
});