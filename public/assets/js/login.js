document.getElementById('form-login').addEventListener('submit', async (e) => {
    e.preventDefault(); // Evita que a página recarregue

    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const msgErro = document.getElementById('msg-erro');

    try {
        // Envia as credenciais para a nossa futura rota Python
        const resposta = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        if (!resposta.ok) {
            throw new Error('Credenciais inválidas');
        }

        const dados = await resposta.json();

        // Salva o token secreto no navegador do administrador
        localStorage.setItem('token_lacorte', dados.token);

        // Redireciona para o painel de administração
        window.location.href = '/admin.html';

    } catch (erro) {
        msgErro.classList.remove('hidden');
    }
});