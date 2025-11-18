#!/usr/bin/env python3
"""
Script de Automação para Remoção de Direitos Autorais do YouTube
Compatível com Windows e Linux - MODO TOTALMENTE AUTOMÁTICO
"""

import sys
import os
import platform
import subprocess
import shutil
import time
import zipfile
import requests
from pathlib import Path

# Detecta o sistema operacional
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

print("="*60)
print("🚀 AUTOMAÇÃO DE REMOÇÃO DE DIREITOS AUTORAIS - YOUTUBE")
print("="*60)
print(f"Sistema operacional: {platform.system()}")
print("="*60)

# ========================
# INSTALAÇÃO DE DEPENDÊNCIAS
# ========================

def instalar_dependencias():
    """Instala todas as dependências necessárias"""
    print("\n📦 Instalando dependências Python...")
    
    dependencias = [
        "selenium",
        "xvfbwrapper",
        "requests",
        "gdown"
    ]
    
    for dep in dependencias:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", dep])
            print(f"✓ {dep} instalado")
        except:
            print(f"⚠ Erro ao instalar {dep}")
    
    if IS_LINUX:
        print("\n📦 Instalando dependências do sistema (Chrome, ChromeDriver, Xvfb)...")
        try:
            # Atualiza repositórios
            subprocess.run(["sudo", "apt-get", "update", "-qq"], check=False)
            
            # Instala Xvfb
            subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", "xvfb"], check=False)
            print("✓ Xvfb instalado")
            
            # Instala Chrome
            subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", "wget"], check=False)
            subprocess.run(["wget", "-q", "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"], check=False)
            subprocess.run(["sudo", "dpkg", "-i", "google-chrome-stable_current_amd64.deb"], check=False)
            subprocess.run(["sudo", "apt-get", "-f", "install", "-y", "-qq"], check=False)
            subprocess.run(["rm", "-f", "google-chrome-stable_current_amd64.deb"], check=False)
            print("✓ Google Chrome instalado")
            
            # Instala ChromeDriver
            subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", "chromium-chromedriver"], check=False)
            print("✓ ChromeDriver instalado")
            
        except Exception as e:
            print(f"⚠ Erro ao instalar dependências do sistema: {e}")
            print("Execute manualmente:")
            print("  sudo apt-get update")
            print("  sudo apt-get install -y xvfb wget google-chrome-stable chromium-chromedriver")

# Instala dependências
instalar_dependencias()

# Importa após instalação
import gdown
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ========================
# FUNÇÕES AUXILIARES
# ========================

def baixar_perfil_chrome():
    """Baixa o perfil do Chrome do Google Drive"""
    print("\n📥 Baixando perfil do Chrome do Google Drive...")
    
    # URL do arquivo no Google Drive
    file_id = "14aThtiWSRSw6jBU94fsFHZXWORUucRJk"
    url = f"https://drive.google.com/uc?id={file_id}"
    
    # Define o caminho para salvar
    if IS_WINDOWS:
        download_dir = os.path.join(os.getenv('TEMP'), 'ChromeProfile')
    else:
        download_dir = '/tmp/ChromeProfile'
    
    # Remove diretório anterior se existir
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
    
    os.makedirs(download_dir, exist_ok=True)
    
    zip_path = os.path.join(download_dir, "profile6.zip")
    
    try:
        # Baixa o arquivo usando gdown
        print("⏳ Baixando arquivo (pode levar alguns minutos)...")
        gdown.download(url, zip_path, quiet=False)
        print("✓ Download concluído!")
        
        # Extrai o arquivo
        print("📂 Extraindo perfil...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)
        
        # Remove o arquivo zip
        os.remove(zip_path)
        print("✓ Perfil extraído com sucesso!")
        
        # Procura pela pasta "Profile 6" (case insensitive)
        profile_path = None
        for item in os.listdir(download_dir):
            if item.lower() == "profile 6":
                profile_path = os.path.join(download_dir, item)
                break
        
        if not profile_path:
            # Se não encontrou, procura qualquer pasta
            for item in os.listdir(download_dir):
                item_path = os.path.join(download_dir, item)
                if os.path.isdir(item_path):
                    profile_path = item_path
                    break
        
        if profile_path:
            print(f"✓ Perfil encontrado: {profile_path}")
            return profile_path
        else:
            print("⚠ Pasta do perfil não encontrada no arquivo extraído")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao baixar perfil: {e}")
        print("Tentando usar perfil local...")
        return None

def preparar_perfil_para_selenium(profile_path):
    """Prepara o perfil baixado para uso com Selenium"""
    if IS_WINDOWS:
        temp_dir = os.path.join(os.getenv('TEMP'), 'ChromeSeleniumProfile')
    else:
        temp_dir = '/tmp/ChromeSeleniumProfile'
    
    # Remove diretório temporário anterior se existir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    os.makedirs(temp_dir)
    
    # Copia o perfil para um diretório "Default" dentro do temp_dir
    dest = os.path.join(temp_dir, "Default")
    
    print(f"\n📋 Preparando perfil para Selenium...")
    shutil.copytree(profile_path, dest, ignore=shutil.ignore_patterns('Service Worker', 'Code Cache'))
    print("✓ Perfil preparado")
    
    return temp_dir

def encontrar_perfis_chrome():
    """Encontra todos os perfis do Chrome disponíveis"""
    if IS_WINDOWS:
        user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
    elif IS_LINUX:
        user_data_dir = os.path.expanduser('~/.config/google-chrome')
    else:
        return None, []
    
    if not os.path.exists(user_data_dir):
        return None, []
    
    perfis = []
    # Procura por "Default" e "Profile X"
    for item in os.listdir(user_data_dir):
        if item == "Default" or item.startswith("Profile "):
            perfil_path = os.path.join(user_data_dir, item)
            if os.path.isdir(perfil_path):
                perfis.append((item, perfil_path))
    
    return user_data_dir, perfis

def selecionar_perfil():
    """Tenta baixar o perfil do Google Drive, senão usa perfil local"""
    # Primeiro tenta baixar o perfil do Google Drive
    profile_path = baixar_perfil_chrome()
    
    if profile_path:
        temp_user_data = preparar_perfil_para_selenium(profile_path)
        print(f"✓ Usando perfil baixado do Google Drive")
        return temp_user_data, True
    
    # Se falhou, tenta usar perfil local
    print("\n🔍 Buscando perfis locais do Chrome...")
    user_data_dir, perfis = encontrar_perfis_chrome()
    
    if not perfis:
        print("\n⚠️ Nenhum perfil do Chrome encontrado!")
        print("O Chrome será aberto sem perfil (você precisará fazer login manualmente)")
        return None, False
    
    # Seleciona automaticamente o primeiro perfil (Default)
    perfil_escolhido = perfis[0]
    print(f"\n✓ Perfil local selecionado: {perfil_escolhido[0]}")
    
    # Cria cópia temporária do perfil local
    if IS_WINDOWS:
        temp_dir = os.path.join(os.getenv('TEMP'), 'ChromeSeleniumProfile')
    else:
        temp_dir = '/tmp/ChromeSeleniumProfile'
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    os.makedirs(temp_dir)
    
    source = os.path.join(user_data_dir, perfil_escolhido[0])
    dest = os.path.join(temp_dir, "Default")
    
    print(f"\n📋 Copiando perfil {perfil_escolhido[0]}...")
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns('Service Worker', 'Code Cache'))
    print("✓ Perfil copiado")
    
    return temp_dir, False

# ========================
# CONFIGURAÇÃO DO CHROME
# ========================

print("\n" + "="*60)
temp_user_data, is_downloaded = selecionar_perfil()

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-first-run")
chrome_options.add_argument("--no-default-browser-check")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Configura perfil se foi selecionado
if temp_user_data:
    chrome_options.add_argument(f"user-data-dir={temp_user_data}")

# ========================
# INICIALIZAÇÃO DO DRIVER
# ========================

print("\n🌐 Inicializando Chrome...")

# Criação de pasta para screenshots
screenshots_dir = f"screenshots_{time.strftime('%Y%m%d_%H%M%S')}"
os.makedirs(screenshots_dir, exist_ok=True)
screenshot_counter = 0

def tirar_screenshot(descricao):
    """Tira um screenshot e salva com descrição"""
    global screenshot_counter
    try:
        screenshot_counter += 1
        filename = os.path.join(screenshots_dir, f"{screenshot_counter:03d}_{descricao}.png")
        driver.save_screenshot(filename)
        print(f"📸 Screenshot salvo: {filename}")
        return True
    except Exception as e:
        print(f"⚠ Erro ao tirar screenshot: {e}")
        return False

# No Linux, usa Xvfb automaticamente para executar sem interface gráfica
if IS_LINUX:
    print("\n🖥️ Iniciando em modo headless com Xvfb...")
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1920, height=1080)
    vdisplay.start()
    print("✓ Xvfb iniciado")
    print(f"📸 Screenshots serão salvos em: {screenshots_dir}/")

# Inicializa o ChromeDriver
try:
    if IS_LINUX:
        # No Linux, tenta usar o chromedriver do sistema
        chromedriver_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            'chromedriver'
        ]
        
        service = None
        for path in chromedriver_paths:
            if os.path.exists(path) or path == 'chromedriver':
                try:
                    service = Service(path)
                    break
                except:
                    continue
        
        if service is None:
            # Se não encontrou, deixa o Selenium procurar
            service = Service()
    else:
        # No Windows, deixa o Selenium encontrar automaticamente
        service = Service()
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)
    print("✓ Chrome iniciado com sucesso!")
except Exception as e:
    print(f"⚠ Aviso ao iniciar com service: {e}")
    print("\nTentando sem service específico...")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)
        print("✓ Chrome iniciado com sucesso!")
    except Exception as e2:
        print(f"❌ Erro crítico ao iniciar Chrome: {e2}")
        print("\nVerifique se o Chrome e ChromeDriver estão instalados:")
        print("  sudo apt-get install google-chrome-stable chromium-chromedriver")
        if IS_LINUX:
            vdisplay.stop()
        sys.exit(1)

# ========================
# FUNÇÕES DE AUTOMAÇÃO
# ========================

def fazer_login():
    """Realiza o login no Google se necessário"""
    try:
        print("\n🔐 Abrindo página de login do Google...")
        driver.get("https://accounts.google.com")
        time.sleep(3)
        tirar_screenshot("01_pagina_login")
        
        # Verifica se já está logado
        if "myaccount.google.com" in driver.current_url:
            print("✓ Login já realizado anteriormente!")
            tirar_screenshot("02_ja_logado")
            return True
            
        print("⚠️ Login necessário - iniciando processo...")
        
        # Preencher email
        email_field = wait.until(EC.element_to_be_clickable((By.ID, "identifierId")))
        email_field.click()
        email_field.clear()
        email_field.send_keys('cmm0909mm@gmail.com')
        time.sleep(1)
        tirar_screenshot("03_email_preenchido")
        email_field.send_keys(Keys.RETURN)
        
        # Preencher senha
        time.sleep(3)
        tirar_screenshot("04_tela_senha")
        password_field = wait.until(EC.element_to_be_clickable((By.NAME, "Passwd")))
        password_field.click()
        password_field.clear()
        password_field.send_keys('Alisson0909jj')
        time.sleep(1)
        tirar_screenshot("05_senha_preenchida")
        password_field.send_keys(Keys.RETURN)
        
        time.sleep(5)
        tirar_screenshot("06_login_concluido")
        print("✓ Login concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        tirar_screenshot("erro_login")
        return False

def excluir_video_atual(video_element):
    """Exclui um vídeo que não pode ter o copyright removido"""
    try:
        print("\n🗑️ Excluindo vídeo...")
        tirar_screenshot("excluir_01_inicio")
        
        checkbox = video_element.find_element(By.CSS_SELECTOR, "ytcp-checkbox-lit")
        checkbox_div = checkbox.find_element(By.CSS_SELECTOR, "div[role='checkbox']")
        
        try:
            checkbox_div.click()
            print("✓ Selecionou o vídeo")
        except:
            driver.execute_script("arguments[0].click();", checkbox_div)
            print("✓ Selecionou o vídeo (via JavaScript)")
        
        time.sleep(2)
        tirar_screenshot("excluir_02_video_selecionado")
        
        mais_acoes = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), 'Mais ações')]/ancestor::div[@role='button']")
        ))
        mais_acoes.click()
        print("✓ Clicou em 'Mais ações'")
        time.sleep(2)
        tirar_screenshot("excluir_03_menu_acoes")
        
        excluir = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//yt-formatted-string[contains(text(), 'Excluir para sempre')]")
        ))
        excluir.click()
        print("✓ Clicou em 'Excluir para sempre'")
        time.sleep(2)
        tirar_screenshot("excluir_04_confirmacao")
        
        checkbox_confirma = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#dialog-content-confirm-checkboxes div[role='checkbox']")
        ))
        
        try:
            checkbox_confirma.click()
            print("✓ Marcou checkbox de confirmação")
        except:
            driver.execute_script("arguments[0].click();", checkbox_confirma)
            print("✓ Marcou checkbox de confirmação (via JavaScript)")
        
        time.sleep(1)
        tirar_screenshot("excluir_05_checkbox_marcado")
        
        botao_excluir = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@aria-label, 'Excluir para sempre')]")
        ))
        botao_excluir.click()
        print("✓ Confirmou exclusão")
        time.sleep(3)
        tirar_screenshot("excluir_06_concluido")
        
        print("✅ Vídeo excluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"⚠ Erro ao excluir vídeo: {e}")
        tirar_screenshot("erro_excluir")
        return False

def processar_video_com_copyright(video_element):
    """Processa um vídeo específico com copyright"""
    try:
        print("\n🔹 Processando vídeo com copyright...")
        tirar_screenshot("video_01_inicio")
        
        # Verifica se o vídeo está bloqueado
        try:
            bloqueado = video_element.find_element(
                By.XPATH,
                ".//span[contains(text(), 'Bloqueado')]"
            )
            if bloqueado:
                print("🚫 Vídeo está BLOQUEADO - será excluído")
                tirar_screenshot("video_02_bloqueado")
                return excluir_video_atual(video_element)
        except:
            pass
        
        restriction_div = video_element.find_element(By.CSS_SELECTOR, "div.restrictions-list")
        
        try:
            direitos_text = restriction_div.find_element(By.ID, "restrictions-text")
            direitos_text.click()
            print("✓ Clicou em 'Direitos autorais'")
        except:
            restriction_div.click()
            print("✓ Clicou na área de restrições")
        
        time.sleep(2)
        tirar_screenshot("video_03_restricoes_clicadas")
        
        try:
            try:
                mais_detalhes = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@aria-label, 'Mais detalhes')]")
                ))
            except:
                try:
                    mais_detalhes = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//ytcp-button//button[.//div[contains(text(), 'Mais detalhes')]]")
                    ))
                except:
                    mais_detalhes = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//ytcp-paper-tooltip-placeholder//button[contains(., 'Mais detalhes')]")
                    ))
            
            mais_detalhes.click()
            print("✓ Clicou em 'Mais detalhes'")
            time.sleep(3)
            tirar_screenshot("video_04_mais_detalhes")
        except Exception as e:
            print(f"⚠ Não encontrou botão 'Mais detalhes': {e}")
            tirar_screenshot("erro_mais_detalhes")
            return False
        
        # Processa múltiplos conteúdos
        conteudos_processados = 0
        while True:
            try:
                time.sleep(2)
                tirar_screenshot(f"conteudo_{conteudos_processados+1:02d}_01_verificando")
                
                # Verifica mensagem "Nenhum conteúdo protegido"
                try:
                    mensagem_sem_conteudo = driver.find_element(
                        By.CSS_SELECTOR,
                        "div.ytcrVideoContentListNoContentMessage"
                    )
                    if mensagem_sem_conteudo and mensagem_sem_conteudo.is_displayed():
                        print("✓ Nenhum conteúdo protegido por direitos autorais foi encontrado no vídeo")
                        tirar_screenshot("video_05_sem_conteudo")
                        break
                except:
                    pass
                
                # Busca conteúdos que precisam de ação
                botoes_disponiveis = []
                try:
                    containers = driver.find_elements(
                        By.CSS_SELECTOR,
                        "div.ytcrVideoContentListContentRowContainer"
                    )
                    
                    for container in containers:
                        try:
                            impact_text = container.find_element(
                                By.CSS_SELECTOR,
                                "div.impact-text"
                            )
                            
                            if "não restringe seu vídeo" in impact_text.text.lower():
                                continue
                            
                            botoes = container.find_elements(
                                By.XPATH,
                                ".//button[contains(@aria-label, 'Tomar providências')]"
                            )
                            
                            for botao in botoes:
                                aria_disabled = botao.get_attribute("aria-disabled")
                                is_disabled = botao.get_attribute("disabled")
                                
                                if aria_disabled == "false" and not is_disabled:
                                    botoes_disponiveis.append(botao)
                                    break
                        except:
                            continue
                    
                    if not botoes_disponiveis:
                        print("✓ Não há mais conteúdos que precisam de ação neste vídeo")
                        tirar_screenshot(f"conteudo_{conteudos_processados+1:02d}_02_sem_acoes")
                        break
                    
                    tomar_providencias = botoes_disponiveis[0]
                    tomar_providencias.click()
                    conteudos_processados += 1
                    print(f"✓ Clicou em 'Tomar providências' (conteúdo #{conteudos_processados})")
                    time.sleep(3)
                    tirar_screenshot(f"conteudo_{conteudos_processados:02d}_03_tomar_providencias")
                    
                except Exception as e:
                    print(f"✓ Não há mais músicas/conteúdos para processar neste vídeo")
                    tirar_screenshot(f"conteudo_{conteudos_processados+1:02d}_04_fim")
                    break
                
                # Tenta remover música ou cortar trecho
                try:
                    remover_musica = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "button[action='NON_TAKEDOWN_CLAIM_OPTION_ERASE_SONG']")
                    ))
                    remover_musica.click()
                    print("✓ Selecionou 'Remover música'")
                    tipo_acao = "remover_musica"
                    tirar_screenshot(f"conteudo_{conteudos_processados:02d}_05_remover_musica")
                except:
                    try:
                        cortar_trecho = wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "button[action='NON_TAKEDOWN_CLAIM_OPTION_TRIM']")
                        ))
                        cortar_trecho.click()
                        print("✓ Selecionou 'Cortar o trecho'")
                        tipo_acao = "cortar_trecho"
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_05_cortar_trecho")
                    except:
                        print("⚠ Não encontrou opção de ação - vídeo será excluído")
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_erro_sem_opcao")
                        actions = ActionChains(driver)
                        actions.send_keys(Keys.ESCAPE).perform()
                        time.sleep(2)
                        return excluir_video_atual(video_element)
                
                time.sleep(2)
                
                # Fluxo de remoção/corte
                if tipo_acao == "remover_musica":
                    try:
                        continuar = wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(@aria-label, 'Continuar')]")
                        ))
                    except:
                        continuar = wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//ytcp-button-shape//button[.//div[contains(text(), 'Continuar')]]")
                        ))
                    continuar.click()
                    print("✓ Clicou em 'Continuar'")
                    time.sleep(3)
                    tirar_screenshot(f"conteudo_{conteudos_processados:02d}_06_continuar")
                    
                    try:
                        try:
                            salvar = wait.until(EC.element_to_be_clickable(
                                (By.XPATH, "//button[contains(@aria-label, 'Salvar')]")
                            ))
                        except:
                            try:
                                salvar = wait.until(EC.element_to_be_clickable(
                                    (By.XPATH, "//ytcp-button-shape//button[.//div[contains(text(), 'Salvar')]]")
                                ))
                            except:
                                salvar = wait.until(EC.element_to_be_clickable(
                                    (By.XPATH, "//*[contains(text(), 'Salvar') and (self::button or ancestor::button)]")
                                ))
                        
                        salvar.click()
                        print("✓ Clicou em 'Salvar'")
                        time.sleep(2)
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_07_salvar_corte")
                    except Exception as e:
                        print(f"⚠ Erro ao clicar em Salvar: {e}")
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_erro_salvar_corte")
                        return False
                
                # Marca checkbox
                try:
                    time.sleep(2)
                    tirar_screenshot(f"conteudo_{conteudos_processados:02d}_08_antes_checkbox")
                    
                    try:
                        checkbox = wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//div[@role='checkbox' and contains(@aria-label, 'Entendo que essas mudanças são permanentes')]")
                        ))
                    except:
                        checkbox = wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div[role='checkbox'][aria-checked='false']")
                        ))
                    
                    try:
                        checkbox.click()
                        print("✓ Marcou a checkbox")
                    except:
                        driver.execute_script("arguments[0].click();", checkbox)
                        print("✓ Marcou a checkbox (via JavaScript)")
                    
                    time.sleep(1)
                    tirar_screenshot(f"conteudo_{conteudos_processados:02d}_09_checkbox_marcado")
                    
                except Exception as e:
                    print(f"⚠ Erro ao marcar checkbox: {e}")
                    tirar_screenshot(f"conteudo_{conteudos_processados:02d}_erro_checkbox")
                    try:
                        checkbox = driver.find_element(By.XPATH, "//div[@role='checkbox' and @aria-checked='false']")
                        driver.execute_script("arguments[0].click();", checkbox)
                        print("✓ Marcou a checkbox (alternativa JS)")
                        time.sleep(1)
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_09_checkbox_alt")
                    except:
                        print("⚠ Não conseguiu marcar a checkbox")
                        return False
                
                # Confirma mudanças
                try:
                    confirmar = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(@aria-label, 'Confirmar mudanças')]")
                    ))
                except:
                    confirmar = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//ytcp-button-shape//button[.//div[contains(text(), 'Confirmar mudanças')]]")
                    ))
                confirmar.click()
                print("✓ Confirmou as mudanças")
                time.sleep(5)
                tirar_screenshot(f"conteudo_{conteudos_processados:02d}_10_confirmado")
                
                # Aguarda processamento
                print("⏳ Aguardando processamento...")
                tentativas = 0
                
                while True:
                    try:
                        try:
                            mensagem = driver.find_element(
                                By.CSS_SELECTOR,
                                "div.ytcrVideoContentListNoContentMessage"
                            )
                            if mensagem and mensagem.is_displayed():
                                print("✓ Processamento concluído! Nenhum conteúdo restante.")
                                tirar_screenshot(f"conteudo_{conteudos_processados:02d}_11_concluido")
                                time.sleep(2)
                                break
                        except:
                            pass
                        
                        botoes = driver.find_elements(
                            By.XPATH,
                            "//button[contains(@aria-label, 'Tomar providências')]"
                        )
                        
                        algum_habilitado = False
                        for botao in botoes:
                            aria_disabled = botao.get_attribute("aria-disabled")
                            is_disabled = botao.get_attribute("disabled")
                            
                            if aria_disabled == "false" and not is_disabled:
                                algum_habilitado = True
                                break
                        
                        if algum_habilitado:
                            print("✓ Processamento concluído!")
                            tirar_screenshot(f"conteudo_{conteudos_processados:02d}_11_pronto")
                            time.sleep(3)
                            break
                            
                    except Exception as e:
                        pass
                    
                    tentativas += 1
                    time.sleep(5)
                    
                    if tentativas % 12 == 0:
                        print(f"⏳ Ainda processando... ({tentativas//12} min)")
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_processando_{tentativas//12}min")
                    
            except Exception as e:
                print(f"⚠ Erro ao processar conteúdo: {e}")
                tirar_screenshot(f"conteudo_{conteudos_processados+1:02d}_erro")
                import traceback
                traceback.print_exc()
                break
        
        # Volta para lista
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(2)
        tirar_screenshot("video_06_voltar_lista")
        print("✓ Voltou para lista de vídeos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar vídeo: {e}")
        tirar_screenshot("erro_processar_video")
        return False

def processar_pagina():
    """Processa todos os vídeos com copyright na página atual"""
    try:
        print("\n🔍 Verificando vídeos na página...")
        time.sleep(3)
        tirar_screenshot("pagina_01_inicio")
        
        videos_com_copyright = []
        rows = driver.find_elements(By.CSS_SELECTOR, "ytcp-video-row")
        
        for row in rows:
            try:
                restriction = row.find_element(By.CSS_SELECTOR, "div.restrictions-list")
                if "Direitos autorais" in restriction.text or "direitos autorais" in restriction.text:
                    videos_com_copyright.append(row)
            except:
                continue
        
        print(f"📊 Encontrados {len(videos_com_copyright)} vídeo(s) com direitos autorais nesta página")
        tirar_screenshot(f"pagina_02_encontrados_{len(videos_com_copyright)}_videos")
        
        for idx, video in enumerate(videos_com_copyright, 1):
            print(f"\n[{idx}/{len(videos_com_copyright)}] Processando vídeo...")
            tirar_screenshot(f"pagina_video_{idx:02d}_inicio")
            processar_video_com_copyright(video)
            time.sleep(2)
            tirar_screenshot(f"pagina_video_{idx:02d}_fim")
        
        return len(videos_com_copyright) > 0
        
    except Exception as e:
        print(f"❌ Erro ao processar página: {e}")
        tirar_screenshot("erro_processar_pagina")
        return False

def proxima_pagina():
    """Vai para a próxima página"""
    try:
        botao_proximo = driver.find_element(
            By.CSS_SELECTOR,
            "ytcp-icon-button[aria-label*='próxima']"
        )
        
        if botao_proximo.get_attribute("aria-disabled") == "true":
            print("\n🔄 Última página alcançada!")
            return False
        
        botao_proximo.click()
        print("\n➡️ Indo para próxima página...")
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"❌ Erro ao ir para próxima página: {e}")
        return False

def voltar_primeira_pagina():
    """Volta para a primeira página"""
    try:
        botao_primeira = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "ytcp-icon-button#navigate-first")
        ))
        botao_primeira.click()
        print("\n⏮️ Voltando para primeira página...")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Erro ao voltar para primeira página: {e}")
        return False

# ========================
# EXECUÇÃO PRINCIPAL
# ========================

try:
    # Login
    if not fazer_login():
        print("❌ Falha no login. Encerrando...")
        driver.quit()
        if IS_LINUX:
            vdisplay.stop()
        sys.exit(1)
    
    # Ir para YouTube Studio com channel ID específico
    print("\n🎬 Acessando YouTube Studio...")
    url_studio = "https://studio.youtube.com/channel/UCHsiyzxJ6v68F_J6DgZA7gw/videos/upload?filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D"
    driver.get(url_studio)
    time.sleep(5)
    tirar_screenshot("studio_01_inicial")
    
    print("\n" + "="*60)
    print("🚀 INICIANDO AUTOMAÇÃO DE REMOÇÃO DE DIREITOS AUTORAIS")
    print("="*60)
    
    # Processa todas as páginas
    pagina_atual = 1
    
    while True:
        print(f"\n{'='*60}")
        print(f"📄 PÁGINA {pagina_atual}")
        print("="*60)
        
        processar_pagina()
        
        if not proxima_pagina():
            print("\n✅ Todas as páginas foram processadas!")
            tirar_screenshot("final_01_todas_paginas")
            break
        
        pagina_atual += 1
    
    # Volta para primeira página
    voltar_primeira_pagina()
    tirar_screenshot("final_02_primeira_pagina")
    
    print("\n" + "="*60)
    print("✅ AUTOMAÇÃO CONCLUÍDA!")
    print("="*60)
    print(f"📊 Total de páginas verificadas: {pagina_atual}")
    print("\n🎉 Todos os vídeos com direitos autorais foram processados!")
    print(f"\n📸 Screenshots salvos em: {screenshots_dir}/")
    print(f"📸 Total de screenshots: {screenshot_counter}")
    
    if IS_LINUX:
        print("\nScript concluído. Encerrando...")
    else:
        print("\nO navegador permanecerá aberto. Pressione Enter para fechar...")
        input()

except KeyboardInterrupt:
    print("\n\n⚠️ Execução interrompida pelo usuário")
    tirar_screenshot("interrupcao_usuario")
except Exception as e:
    print(f"\n❌ Ocorreu um erro: {e}")
    tirar_screenshot("erro_geral")
    import traceback
    traceback.print_exc()
    if not IS_LINUX:
        print("\nO navegador permanecerá aberto. Pressione Enter para fechar...")
        input()

finally:
    try:
        driver.quit()
        print("Navegador fechado.")
    except:
        pass
    
    if IS_LINUX:
        try:
            vdisplay.stop()
            print("Xvfb encerrado.")
        except:
            pass
    
    print(f"\n📸 Todos os screenshots foram salvos em: {screenshots_dir}/")
    print(f"📸 Total de screenshots capturados: {screenshot_counter}")"conteudo_{conteudos_processados:02d}_07_salvar")
                    except Exception as e:
                        print(f"⚠ Erro ao clicar em Salvar: {e}")
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_erro_salvar")
                        return False
                
                elif tipo_acao == "cortar_trecho":
                    try:
                        try:
                            continuar = wait.until(EC.element_to_be_clickable(
                                (By.XPATH, "//button[contains(@aria-label, 'Continuar')]")
                            ))
                        except:
                            continuar = wait.until(EC.element_to_be_clickable(
                                (By.XPATH, "//ytcp-button-shape//button[.//div[contains(text(), 'Continuar')]]")
                            ))
                        continuar.click()
                        print("✓ Clicou em 'Continuar'")
                        time.sleep(3)
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_06_continuar_corte")
                    except Exception as e:
                        print(f"⚠ Erro ao clicar em Continuar: {e}")
                        tirar_screenshot(f"conteudo_{conteudos_processados:02d}_erro_continuar")
                        return False
                    
                    try:
                        try:
                            salvar = wait.until(EC.element_to_be_clickable(
                                (By.XPATH, "//button[contains(@aria-label, 'Salvar')]")
                            ))
                        except:
                            try:
                                salvar = wait.until(EC.element_to_be_clickable(
                                    (By.XPATH, "//ytcp-button-shape//button[.//div[contains(text(), 'Salvar')]]")
                                ))
                            except:
                                salvar = wait.until(EC.element_to_be_clickable(
                                    (By.XPATH, "//*[contains(text(), 'Salvar') and (self::button or ancestor::button)]")
                                ))
                        
                        salvar.click()
                        print("✓ Clicou em 'Salvar'")
                        time.sleep(2)
                        tirar_screenshot(f
