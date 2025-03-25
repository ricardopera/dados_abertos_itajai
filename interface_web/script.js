document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('consultaForm');
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');
    
    // Função para validar formato de data DD/MM/AAAA
    function validarData(data) {
        const regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
        if (!regex.test(data)) return false;
        
        const partes = data.split('/');
        const dia = parseInt(partes[0], 10);
        const mes = parseInt(partes[1], 10) - 1;
        const ano = parseInt(partes[2], 10);
        
        const dataObj = new Date(ano, mes, dia);
        return dataObj.getDate() === dia && 
               dataObj.getMonth() === mes && 
               dataObj.getFullYear() === ano;
    }
    
    // Função para validar matrícula (somente números)
    function validarMatricula(matricula) {
        return /^\d+$/.test(matricula);
    }
    
    // Validação de campos ao sair do input
    document.getElementById('data_inicio').addEventListener('blur', function(e) {
        if (this.value && !validarData(this.value)) {
            this.classList.add('invalid');
            alert('Data inicial inválida. Use o formato DD/MM/AAAA');
            this.focus();
        } else {
            this.classList.remove('invalid');
        }
    });
    
    document.getElementById('data_fim').addEventListener('blur', function(e) {
        if (this.value && !validarData(this.value)) {
            this.classList.add('invalid');
            alert('Data final inválida. Use o formato DD/MM/AAAA');
            this.focus();
        } else {
            this.classList.remove('invalid');
        }
    });
    
    document.getElementById('matricula').addEventListener('blur', function(e) {
        if (this.value && !validarMatricula(this.value)) {
            this.classList.add('invalid');
            alert('Matrícula inválida. Use somente números.');
            this.focus();
        } else {
            this.classList.remove('invalid');
        }
    });
    
    // Extrair a validação do formulário em uma função para reutilizar
    function validarFormulario(matricula, dataInicio, dataFim) {
        // Validar matrícula
        if (!validarMatricula(matricula)) {
            alert('Matrícula inválida. Use somente números.');
            return false;
        }
        
        // Validar datas
        if (!validarData(dataInicio)) {
            alert('Data inicial inválida. Use o formato DD/MM/AAAA');
            return false;
        }
        
        if (!validarData(dataFim)) {
            alert('Data final inválida. Use o formato DD/MM/AAAA');
            return false;
        }
        
        // Verificar se a data final é maior que a inicial
        const partesInicio = dataInicio.split('/');
        const partesFim = dataFim.split('/');
        const dateInicio = new Date(
            parseInt(partesInicio[2]), 
            parseInt(partesInicio[1]) - 1, 
            parseInt(partesInicio[0])
        );
        const dateFim = new Date(
            parseInt(partesFim[2]), 
            parseInt(partesFim[1]) - 1, 
            parseInt(partesFim[0])
        );
        
        if (dateFim < dateInicio) {
            alert('A data final deve ser maior ou igual à data inicial.');
            return false;
        }
        
        return true;
    }
    
    // Manipulador do envio do formulário
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const matricula = document.getElementById('matricula').value;
        const dataInicio = document.getElementById('data_inicio').value;
        const dataFim = document.getElementById('data_fim').value;
        
        // Validar novamente antes de enviar
        if (!validarFormulario(matricula, dataInicio, dataFim)) {
            return;
        }
        
        // Mostrar loading e esconder erro
        loadingElement.classList.remove('hidden');
        errorElement.classList.add('hidden');
        
        // Construir a URL com os parâmetros
        const url = "https://dados-abertos-itajai.azurewebsites.net/api/gerar_relatorio_matricula";
        const params = `?matricula=${matricula}&start_date=${dataInicio}&end_date=${dataFim}`;
        
        // Atualizar o link direto
        const linkDireto = document.getElementById('linkDireto');
        linkDireto.href = url + params;
        
        // Adicionar evento de análise apenas quando o site estiver hospedado no GitHub
        if (window.location.hostname.includes('github.io')) {
            console.log('Site hospedado no GitHub Pages - usando link direto como alternativa');
        }
        
        // Fazer o download do arquivo
        downloadArquivo(url + params);
    });
    
    // Configurar o link direto para abrir em uma nova aba
    document.getElementById('linkDireto').addEventListener('click', function(e) {
        const matricula = document.getElementById('matricula').value;
        const dataInicio = document.getElementById('data_inicio').value;
        const dataFim = document.getElementById('data_fim').value;
        
        if (!validarFormulario(matricula, dataInicio, dataFim)) {
            e.preventDefault();
            return;
        }
        
        const url = "https://dados-abertos-itajai.azurewebsites.net/api/gerar_relatorio_matricula";
        const params = `?matricula=${matricula}&start_date=${dataInicio}&end_date=${dataFim}`;
        
        this.href = url + params;
    });
    
    // Botão "Tentar Novamente"
    document.getElementById('btnTentarNovamente').addEventListener('click', function() {
        errorElement.classList.add('hidden');
        form.dispatchEvent(new Event('submit'));
    });
    
    // Função para lidar com o download do arquivo
    function downloadArquivo(url) {
        const a = document.createElement('a');
        a.style.display = 'none';
        document.body.appendChild(a);
        
        // Extrair os parâmetros da URL para usar no nome do arquivo
        const urlParams = new URLSearchParams(url.substring(url.indexOf('?')));
        const matricula = urlParams.get('matricula');
        const dataInicio = urlParams.get('start_date');
        const dataFim = urlParams.get('end_date');
        
        // Formatar as datas para MM-AAAA
        const formatarDataParaMesAno = (dataStr) => {
            const partes = dataStr.split('/');
            if (partes.length === 3) {
                return `${partes[1]}-${partes[2]}`;
            }
            return '';
        };
        
        const periodoInicio = formatarDataParaMesAno(dataInicio);
        const periodoFim = formatarDataParaMesAno(dataFim);
        
        // Nome personalizado para o arquivo
        const nomeArquivoCustomizado = `relatorio_matricula_${matricula}_${periodoInicio}_a_${periodoFim}.xlsx`;
        
        // Fazer a requisição com fetch para lidar com erros
        fetch(url, {
            method: 'GET',
            mode: 'cors', // Definir explicitamente o modo CORS
            headers: {
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            credentials: 'omit' // Não enviar cookies para evitar problemas com CORS preflight
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro na requisição: ${response.status} - ${response.statusText}`);
            }
            
            // Obter o nome do arquivo do header Content-Disposition, mas dar preferência ao nome personalizado
            let fileName = nomeArquivoCustomizado;
            
            return response.blob().then(blob => ({blob, fileName}));
        })
        .then(({blob, fileName}) => {
            const url = window.URL.createObjectURL(blob);
            a.href = url;
            a.download = fileName;
            a.click();
            window.URL.revokeObjectURL(url);
            loadingElement.classList.add('hidden');
        })
        .catch(error => {
            console.error('Erro ao baixar o arquivo:', error);
            loadingElement.classList.add('hidden');
            errorElement.classList.remove('hidden');
            
            if (error.name === "TypeError") {
                errorMessage.innerHTML = `
                <p>Problema de acesso à API: O servidor não permite requisições deste site.</p>
                <p>Tente uma das seguintes opções:</p>
                <ul>
                    <li>Entre em contato com o administrador do sistema para habilitar CORS</li>
                    <li>Use a <a href="${url}" target="_blank">URL direta</a> para baixar o arquivo</li>
                </ul>`;
            } else {
                errorMessage.textContent = `Erro ao processar a solicitação: ${error.message}`;
            }
        })
        .finally(() => {
            document.body.removeChild(a);
        });
    }
    
    // Formatação automática de data
    function formatarData(input) {
        let valor = input.value.replace(/\D/g, '');
        
        if (valor.length > 8) {
            valor = valor.substring(0, 8);
        }
        
        if (valor.length > 4) {
            valor = valor.substring(0, 2) + '/' + valor.substring(2, 4) + '/' + valor.substring(4);
        } else if (valor.length > 2) {
            valor = valor.substring(0, 2) + '/' + valor.substring(2);
        }
        
        input.value = valor;
    }
    
    // Aplicar formatação automática nos campos de data
    const dataInicio = document.getElementById('data_inicio');
    const dataFim = document.getElementById('data_fim');
    
    dataInicio.addEventListener('input', function() {
        formatarData(this);
    });
    
    dataFim.addEventListener('input', function() {
        formatarData(this);
    });
});
