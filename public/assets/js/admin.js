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
// 2. DASHBOARD INTELIGENTE
// ==========================================
async function carregarDashboard() {
    try {
        const hoje = hojeISO();
        const dataAtual = new Date();
        const primeiroDiaMes = new Date(dataAtual.getFullYear(), dataAtual.getMonth(), 1).toISOString().split('T')[0];
        const ultimoDiaMes = new Date(dataAtual.getFullYear(), dataAtual.getMonth() + 1, 0).toISOString().split('T')[0];

        // Dispara as requisições simultaneamente (mais rápido)
        const [resumoHoje, resumoMes, agendamentosHoje] = await Promise.all([
            api.get(`/financeiro/resumo?data_inicio=${hoje}&data_fim=${hoje}`),
            api.get(`/financeiro/resumo?data_inicio=${primeiroDiaMes}&data_fim=${ultimoDiaMes}`),
            api.get(`/agendamentos?data=${hoje}`)
        ]);

        const faturamentoHoje = resumoHoje.entradas || 0;
        const faturamentoMes = resumoMes.entradas || 0;
        
        // Conta serviços e calcula ticket médio
        const concluidos = agendamentosHoje ? agendamentosHoje.filter(a => a.status === 'concluido').length : 0;
        const agendados = agendamentosHoje ? agendamentosHoje.length : 0;
        const ticketMedio = concluidos > 0 ? faturamentoHoje / concluidos : 0;

        // Atualiza a Tela
        const els = {
            fatHoje: document.getElementById("valor-faturamento"),
            cortes: document.getElementById("qtd-cortes"),
            agendados: document.getElementById("qtd-agendados"),
            ticket: document.getElementById("valor-ticket"),
            fatMes: document.getElementById("valor-faturamento-mes")
        };

        if(els.fatHoje) {
            els.fatHoje.textContent = formatarPreco(faturamentoHoje);
            els.fatHoje.classList.replace("text-gray-500", "text-white");
            
            els.cortes.textContent = concluidos;
            els.cortes.classList.replace("text-gray-500", "text-white");
            els.agendados.textContent = `Agendados: ${agendados}`;
            
            els.ticket.textContent = formatarPreco(ticketMedio);
            els.ticket.classList.replace("text-gray-500", "text-white");
            
            els.fatMes.textContent = formatarPreco(faturamentoMes);
            els.fatMes.classList.replace("text-gray-500", "text-white");
        }

    } catch (e) {
        console.error("Erro ao carregar o dashboard:", e);
    }
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
                // A cor "text-verde-destaque" corrige o problema de leitura
                tbody.innerHTML = servicos.map(s => `
                    <tr class="border-b border-gray-800 hover:bg-chumbo-claro transition-colors">
                        <td class="p-4 text-sm font-medium text-white">${s.nome}</td>
                        <td class="p-4 text-sm text-verde-destaque font-bold">R$ ${Number(s.preco).toFixed(2).replace('.', ',')}</td>
                        <td class="p-4 text-center">
                            <button onclick="excluirServico(${s.id})" class="text-red-500 hover:text-red-400 text-xs uppercase tracking-wider">Excluir</button>
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

// Cadastro de Serviço
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
            alert("Falha ao salvar. O servidor disse: " + (e.message || JSON.stringify(e)));
        } finally {
            btnSubmit.innerHTML = textoOriginal;
        }
    });
}

// Excluir Serviço (Versão aprimorada com fetch nativo)
window.excluirServico = async function(id) {
    if(confirm("Deseja excluir este serviço? O site dos clientes também será atualizado.")) {
        try {
            // Usando o fetch nativo do navegador para contornar o api.js
            const resposta = await fetch(`/api/servicos/${id}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!resposta.ok) {
                throw new Error(`Erro ${resposta.status}: A rota de exclusão no Python falhou ou não existe.`);
            }

            alert("Serviço excluído com sucesso!");
            await carregarServicos(); // Atualiza a tabela na hora
            
        } catch(e) {
            console.error("Erro completo:", e);
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
                categoria: metodoPagamento,
                valor: valorServico,
                descricao: nomeServico
            });
            formPdv.reset();
            await carregarDashboard(); 
        } catch (erro) {
            alert("Erro ao registrar a venda: " + erro.message);
        } finally {
            btnSubmit.innerHTML = textoOriginal;
        }
    });
}

// Inicia tudo
document.addEventListener("DOMContentLoaded", () => {
    carregarDashboard();
    carregarServicos();
});