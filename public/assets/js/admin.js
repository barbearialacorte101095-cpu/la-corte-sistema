// ==========================================
// 1. SISTEMA DE SEGURANÇA
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
// 2. CARREGAMENTO DOS DADOS (DASHBOARD)
// ==========================================
async function carregarResumo() {
    try {
        const resumo = await api.get(`/financeiro/resumo?data_inicio=${hojeISO()}&data_fim=${hojeISO()}`);
        const faturamentoEl = document.getElementById("valor-faturamento");
        if (faturamentoEl) {
            faturamentoEl.textContent = formatarPreco(resumo.entradas || 0);
            faturamentoEl.classList.replace("text-gray-500", "text-white");
        }
    } catch (e) {
        console.error("Erro no resumo:", e);
    }
}

async function carregarAgendaDoDia() {
    try {
        const agendamentos = await api.get(`/agendamentos?data=${hojeISO()}`);
        const qtdCortesEl = document.getElementById('qtd-cortes');
        const qtdAgendadosEl = document.getElementById('qtd-agendados');
        
        if (qtdCortesEl && qtdAgendadosEl) {
            const concluidos = agendamentos.filter(a => a.status === 'concluido').length;
            qtdCortesEl.textContent = concluidos;
            qtdCortesEl.classList.replace("text-gray-500", "text-white");
            qtdAgendadosEl.textContent = `Agendados: ${agendamentos.length}`;
        }
    } catch (e) {
        console.error("Erro na agenda:", e);
    }
}

async function carregarServicos() {
    try {
        const servicos = await api.get('/servicos');
        const tbody = document.getElementById('lista-servicos-tabela');
        const selectPdv = document.getElementById('pdv-servico');
        
        // Verifica se a tabela existe na tela
        if (tbody) {
            if (!servicos || servicos.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-gray-500">Nenhum serviço cadastrado.</td></tr>`;
            } else {
                tbody.innerHTML = servicos.map(s => `
                    <tr class="border-b border-gray-800 hover:bg-chumbo-claro transition-colors">
                        <td class="p-4 text-sm font-medium text-white">${s.nome}</td>
                        <td class="p-4 text-sm text-verde-corte font-bold">R$ ${Number(s.preco).toFixed(2).replace('.', ',')}</td>
                        <td class="p-4 text-center">
                            <button onclick="excluirServico(${s.id})" class="text-red-500 hover:text-red-400 text-xs uppercase tracking-wider">Excluir</button>
                        </td>
                    </tr>
                `).join('');
            }
        }

        // Atualiza as opções do Frente de Caixa
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

// ==========================================
// 3. AÇÕES DOS FORMULÁRIOS (SALVAR/RECEBER)
// ==========================================

// Frente de Caixa (PDV)
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
                categoria: metodoPagamento,
                valor: valorServico,
                descricao: nomeServico
            });
            formPdv.reset();
            await carregarResumo(); 
            alert("Venda registrada com sucesso!");
        } catch (erro) {
            alert("Erro ao registrar a venda: " + erro.message);
        } finally {
            btnSubmit.innerHTML = textoOriginal;
        }
    });
}

// Cadastro de Serviços
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
            // Tenta salvar o serviço na API
            await api.post('/servicos', { 
                nome: nome, 
                preco: preco,
                duracao_minutos: 30,
                descricao: ""
            });
            
            formNovoServico.reset();
            await carregarServicos(); 
            alert("Serviço cadastrado com sucesso!");
            
        } catch (e) {
            console.error("Erro detalhado:", e);
            // Mostra o erro exato na tela se o Python rejeitar
            alert("Falha ao salvar. O servidor disse: " + (e.message || JSON.stringify(e)));
        } finally {
            btnSubmit.innerHTML = textoOriginal;
        }
    });
}

// Excluir Serviço
window.excluirServico = async function(id) {
    if(confirm("Deseja excluir este serviço? O site dos clientes também será atualizado.")) {
        try {
            await api.delete(`/servicos/${id}`);
            await carregarServicos();
        } catch(e) {
            alert("Erro ao excluir o serviço.");
        }
    }
};

// ==========================================
// 4. INICIAR O SISTEMA AO ABRIR A TELA
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    carregarResumo();
    carregarAgendaDoDia();
    carregarServicos();
});