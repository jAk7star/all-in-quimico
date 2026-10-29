#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
GERADOR DE MATERIAIS DE MESA — ALL-IN QUÍMICO
================================================================================
Gera arquivos HTML para impressão em folhas A4:
  1. CÉDULAS DE DINHEIRO (63mm x 45mm, 18 por folha A4, R$ 100, R$ 50, R$ 10)
  2. FICHAS DE APOSTA (63mm x 45mm, 18 por folha A4, Grupos 1 a 5 com silhuetas)
  3. AMOSTRAGENS RÁPIDAS para auditoria pré-impressão

Desenvolvido para eliminar qualquer erro de renderização em PDF/impressão:
  - Margens perfeitas A4 (10.5mm lateral, 13.5mm vertical)
  - Cores forçadas via -webkit-print-color-adjust: exact
  - Guias de corte externas (crop marks) milimétricas fora da área útil
  - Quebra de página controlada por CSS sem páginas em branco
================================================================================
"""

import sys
import os
import math

# ==============================================================================
# ESTILOS CSS BASE COMPARTILHADOS (BLINDAGEM CONTRA FALHAS DE IMPRESSÃO)
# ==============================================================================

CSS_PRINT_CORE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800;900&display=swap');

:root {
  --font-main: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-heading: 'Outfit', 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Medidas Milimétricas Oficiais (Grid 3x6 = 18 itens por A4) */
  --item-width: 63mm;
  --item-height: 45mm;

  /* Tipografia e Contraste */
  --ink-primary: #0f172a;
  --ink-secondary: #334155;
  --ink-muted: #64748b;
  --ink-faint: #94a3b8;
  --line-hairline: #cbd5e1;
  --line-strong: #0f172a;

  /* Paleta Cédulas */
  --c-100: #0284c7;
  --bg-100: #f0f9ff;
  --bdr-100: #bae6fd;

  --c-50: #d97706;
  --bg-50: #fffbeb;
  --bdr-50: #fde68a;

  --c-10: #16a34a;
  --bg-10: #f0fdf4;
  --bdr-10: #bbf7d0;

  /* Paleta Fichas de Aposta (5 Grupos / Animais) */
  --g1-color: #1d4ed8; /* Coelho - Azul */
  --g1-bg: #eff6ff;
  --g1-border: #bfdbfe;

  --g2-color: #047857; /* Elefante - Esmeralda */
  --g2-bg: #ecfdf5;
  --g2-border: #a7f3d0;

  --g3-color: #b45309; /* Ursinho - Âmbar */
  --g3-bg: #fffbeb;
  --g3-border: #fde68a;

  --g4-color: #6d28d9; /* Tigre - Violeta */
  --g4-bg: #f5f3ff;
  --g4-border: #ddd6fe;

  --g5-color: #b91c1c; /* Cão - Carmim */
  --g5-bg: #fef2f2;
  --g5-border: #fecaca;
}

@page {
  size: A4 portrait;
  margin: 0;
}

* {
  box-sizing: border-box;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

body {
  font-family: var(--font-main);
  background-color: #f1f5f9;
  color: var(--ink-primary);
  margin: 0;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  -webkit-font-smoothing: antialiased;
}

/* Painel de Controle na Tela */
.no-print-bar {
  background: #ffffff;
  padding: 16px 24px;
  border-radius: 10px;
  border: 1px solid var(--line-hairline);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
  text-align: center;
  max-width: 760px;
  width: 90%;
}

.no-print-bar h1 {
  margin: 0 0 6px 0;
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--ink-primary);
}

.no-print-bar p {
  margin: 0 0 14px 0;
  font-size: 0.85rem;
  color: var(--ink-muted);
  line-height: 1.5;
}

.print-btn {
  background: #0f172a;
  color: #ffffff;
  border: none;
  padding: 10px 22px;
  font-family: var(--font-main);
  font-weight: 700;
  font-size: 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
  transition: all 0.15s ease;
}

.print-btn:hover {
  background: #1e293b;
  transform: translateY(-1px);
}

@media print {
  body {
    background-color: transparent !important;
    padding: 0 !important;
  }
  .no-print-bar {
    display: none !important;
  }
  .page {
    box-shadow: none !important;
    margin: 0 !important;
    page-break-after: always;
    break-after: page;
  }
}

/* Folha A4 Padrão (210mm x 297mm) */
.page {
  width: 210mm;
  height: 297mm;
  position: relative;
  background: #ffffff;
  margin: 15px auto;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  page-break-inside: avoid;
  break-inside: avoid;
}

/* Guias de Corte Externas Milimétricas (0.4pt Hairline) */
.crop-mark {
  position: absolute;
  pointer-events: none;
  background-color: #334155;
}
.crop-v {
  width: 0.4pt;
  height: 8mm;
}
.crop-h {
  height: 0.4pt;
  width: 8mm;
}

/* Posições das guias verticais (Colunas: 10.5mm, 73.5mm, 136.5mm, 199.5mm) */
.crop-v-top-0 { top: 2.5mm; left: 10.5mm; }
.crop-v-top-1 { top: 2.5mm; left: 73.5mm; }
.crop-v-top-2 { top: 2.5mm; left: 136.5mm; }
.crop-v-top-3 { top: 2.5mm; left: 199.5mm; }

.crop-v-bot-0 { bottom: 2.5mm; left: 10.5mm; }
.crop-v-bot-1 { bottom: 2.5mm; left: 73.5mm; }
.crop-v-bot-2 { bottom: 2.5mm; left: 136.5mm; }
.crop-v-bot-3 { bottom: 2.5mm; left: 199.5mm; }

/* Posições das guias horizontais (Linhas: 13.5, 58.5, 103.5, 148.5, 193.5, 238.5, 283.5mm) */
.crop-h-l-0 { left: 1mm; top: 13.5mm; }
.crop-h-l-1 { left: 1mm; top: 58.5mm; }
.crop-h-l-2 { left: 1mm; top: 103.5mm; }
.crop-h-l-3 { left: 1mm; top: 148.5mm; }
.crop-h-l-4 { left: 1mm; top: 193.5mm; }
.crop-h-l-5 { left: 1mm; top: 238.5mm; }
.crop-h-l-6 { left: 1mm; top: 283.5mm; }

.crop-h-r-0 { right: 1mm; top: 13.5mm; }
.crop-h-r-1 { right: 1mm; top: 58.5mm; }
.crop-h-r-2 { right: 1mm; top: 103.5mm; }
.crop-h-r-3 { right: 1mm; top: 148.5mm; }
.crop-h-r-4 { right: 1mm; top: 193.5mm; }
.crop-h-r-5 { right: 1mm; top: 238.5mm; }
.crop-h-r-6 { right: 1mm; top: 283.5mm; }

/* Grid 3x6 Centralizado (189mm x 270mm) */
.grid-sheet {
  position: absolute;
  top: 13.5mm;
  left: 10.5mm;
  width: 189mm;
  height: 270mm;
  display: grid;
  grid-template-columns: repeat(3, 63mm);
  grid-template-rows: repeat(6, 45mm);
}

.page-footer-label {
  position: absolute;
  bottom: 4mm;
  left: 10.5mm;
  right: 10.5mm;
  display: flex;
  justify-content: space-between;
  font-size: 5.5pt;
  color: var(--ink-faint);
  font-family: var(--font-mono);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
"""

CSS_CEDULAS = """
/* ========================================================================== */
/* ESTILOS ESPECÍFICOS DAS CÉDULAS (63mm x 45mm — 2 ZONAS)                    */
/* ========================================================================== */

.money-card {
  width: 63mm;
  height: 45mm;
  position: relative;
  display: grid;
  grid-template-columns: 12mm 51mm;
  border: 0.4pt solid #cbd5e1;
  background-color: #ffffff;
  overflow: hidden;
  box-sizing: border-box;
}

/* ZONA 1: FAIXA DE SEGURANÇA VERTICAL (12mm) */
.money-sec {
  width: 12mm;
  height: 45mm;
  background: #f8fafc;
  border-right: 0.4pt solid #cbd5e1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  padding: 1.5mm 0.5mm;
  position: relative;
  overflow: hidden;
}

.money-sec .sec-val-top,
.money-sec .sec-val-bot {
  font-family: var(--font-heading);
  font-weight: 900;
  font-size: 6.5pt;
  line-height: 1;
  letter-spacing: -0.02em;
}

.sec-wave {
  width: 8mm;
  height: 18mm;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.85;
}

.sec-micro {
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  font-family: var(--font-mono);
  font-size: 3.2pt;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--ink-muted);
  white-space: nowrap;
  line-height: 1;
}

/* ZONA 2: CORPO CIENTÍFICO E INSTITUCIONAL (51mm) */
.money-body {
  width: 51mm;
  height: 45mm;
  padding: 1.8mm 2.2mm 1.5mm 2.2mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  background: #ffffff;
  overflow: hidden;
}

/* Fundo guilloché sutil */
.money-watermark-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.05;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.money-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-bottom: 0.5pt solid var(--ink-primary);
  padding-bottom: 0.8mm;
  position: relative;
  z-index: 2;
}

.money-header .inst-title {
  font-family: var(--font-heading);
  font-size: 4.8pt;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--ink-primary);
  text-transform: uppercase;
}

.money-header .kit-badge {
  font-family: var(--font-mono);
  font-size: 4.2pt;
  font-weight: 700;
  color: var(--ink-muted);
  text-transform: uppercase;
}

/* Miolo: Diagrama Científico + Valor Monumental */
.money-mid {
  display: grid;
  grid-template-columns: 24mm 22mm;
  gap: 1mm;
  align-items: center;
  position: relative;
  z-index: 2;
  margin: 0.5mm 0;
}

.sci-diagram-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.sci-diagram-box svg {
  width: 22mm;
  height: 16mm;
}

.sci-tag {
  font-family: var(--font-mono);
  font-size: 3.2pt;
  font-weight: 700;
  color: var(--ink-secondary);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  margin-top: 0.5mm;
  text-align: center;
  line-height: 1.1;
}

.money-val-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  text-align: right;
}

.val-currency {
  font-family: var(--font-heading);
  font-size: 5.5pt;
  font-weight: 800;
  color: var(--ink-muted);
  margin-right: 1mm;
}

.val-big {
  font-family: var(--font-heading);
  font-size: 18pt;
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -0.04em;
}

.val-extenso {
  font-family: var(--font-mono);
  font-size: 3.8pt;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 1mm;
}

/* Rodapé: Serial e Assinatura */
.money-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-top: 0.4pt solid var(--line-hairline);
  padding-top: 0.8mm;
  position: relative;
  z-index: 2;
}

.serial-code {
  font-family: var(--font-mono);
  font-size: 4pt;
  font-weight: 700;
  color: var(--ink-secondary);
}

.signer-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.signer-sig {
  font-family: 'Brush Script MT', cursive, sans-serif;
  font-size: 6.5pt;
  line-height: 0.9;
  color: var(--ink-primary);
  opacity: 0.85;
}

.signer-title {
  font-family: var(--font-main);
  font-size: 3pt;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Temas por valor */
.card-100 {
  border-color: #93c5fd;
}
.card-100 .money-sec {
  background: var(--bg-100);
  border-right-color: var(--bdr-100);
}
.card-100 .sec-val-top,
.card-100 .sec-val-bot,
.card-100 .val-big,
.card-100 .sec-wave svg {
  color: var(--c-100);
}
.card-100 .val-extenso {
  color: var(--c-100);
}

.card-50 {
  border-color: #fcd34d;
}
.card-50 .money-sec {
  background: var(--bg-50);
  border-right-color: var(--bdr-50);
}
.card-50 .sec-val-top,
.card-50 .sec-val-bot,
.card-50 .val-big,
.card-50 .sec-wave svg {
  color: var(--c-50);
}
.card-50 .val-extenso {
  color: var(--c-50);
}

.card-10 {
  border-color: #86efac;
}
.card-10 .money-sec {
  background: var(--bg-10);
  border-right-color: var(--bdr-10);
}
.card-10 .sec-val-top,
.card-10 .sec-val-bot,
.card-10 .val-big,
.card-10 .sec-wave svg {
  color: var(--c-10);
}
.card-10 .val-extenso {
  color: var(--c-10);
}
"""

CSS_FICHAS = """
/* ========================================================================== */
/* ESTILOS CONVENCIONAIS DE FICHAS DE APOSTA / GAMING TOKENS (63mm x 45mm)    */
/* ========================================================================== */

.ficha-card {
  width: 63mm;
  height: 45mm;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 2.2mm 2.5mm 1.8mm 2.5mm;
  border: 0.6pt solid var(--ficha-border);
  background-color: #ffffff;
  overflow: hidden;
  box-sizing: border-box;
}

/* Moldura Interna Pontilhada de Segurança (Token Bezel / Rim) */
.ficha-card::after {
  content: '';
  position: absolute;
  top: 1mm;
  left: 1mm;
  right: 1mm;
  bottom: 1mm;
  border: 0.4pt dashed var(--ficha-border);
  border-radius: 2px;
  pointer-events: none;
  z-index: 3;
}

/* Textura Geométrica de Segurança de Fundo (Guilloché / Micro-Hachura) */
.ficha-texture-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.04;
  pointer-events: none;
  z-index: 1;
}

/* Medalhão Central com a Silhueta do Animal (12% a 14% opacidade) */
.ficha-silhouette-bg {
  position: absolute;
  top: 52%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 32mm;
  height: 32mm;
  opacity: 0.12;
  pointer-events: none;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ficha-silhouette-bg svg {
  width: 100%;
  height: 100%;
  fill: var(--ficha-color);
}

/* 1. TOPO DA FICHA: IDENTIFICAÇÃO INSTITUCIONAL & RODADA */
.ficha-header {
  position: relative;
  z-index: 4;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 0.6pt solid var(--ficha-color);
  padding-bottom: 1mm;
}

.ficha-group-badge {
  display: flex;
  align-items: center;
  gap: 1.5mm;
}

.ficha-group-icon {
  width: 5.2mm;
  height: 5.2mm;
  background: var(--ficha-bg);
  border: 0.4pt solid var(--ficha-border);
  border-radius: 50%;
  padding: 0.5mm;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ficha-group-icon svg {
  width: 100%;
  height: 100%;
  fill: var(--ficha-color);
}

.ficha-group-text {
  display: flex;
  flex-direction: column;
}

.ficha-group-name {
  font-family: var(--font-heading);
  font-size: 5.6pt;
  font-weight: 900;
  letter-spacing: 0.05em;
  color: var(--ficha-color);
  text-transform: uppercase;
  line-height: 1;
}

.ficha-group-animal {
  font-family: var(--font-mono);
  font-size: 3.8pt;
  font-weight: 700;
  color: var(--ink-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  line-height: 1.1;
  margin-top: 0.2mm;
}

.ficha-round-box {
  display: flex;
  align-items: center;
  background: var(--ficha-bg);
  border: 0.5pt solid var(--ficha-border);
  border-radius: 3px;
  padding: 0.6mm 1.8mm;
}

.round-label {
  font-family: var(--font-mono);
  font-size: 3.8pt;
  font-weight: 800;
  color: var(--ficha-color);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 1.2mm;
}

.round-line {
  display: inline-block;
  width: 7mm;
  border-bottom: 0.8pt solid var(--ink-primary);
  height: 3mm;
}

/* 2. ÁREA DE ALTERNATIVAS CONVENCIONAIS [ A ] ou [ B ] */
.ficha-choices-section {
  position: relative;
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0.8mm 0;
}

.choices-prompt {
  font-family: var(--font-mono);
  font-size: 3.5pt;
  font-weight: 800;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 1mm;
}

.choices-container {
  display: flex;
  justify-content: center;
  gap: 5.5mm;
  width: 100%;
}

.choice-box {
  display: flex;
  align-items: center;
  gap: 2mm;
  padding: 1.2mm 4mm;
  border: 0.9pt solid var(--ink-primary);
  border-radius: 4px;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.choice-circle {
  width: 4.2mm;
  height: 4.2mm;
  border-radius: 50%;
  border: 1.1pt solid var(--ink-primary);
  background: #ffffff;
}

.choice-letter {
  font-family: var(--font-heading);
  font-size: 10pt;
  font-weight: 900;
  color: var(--ink-primary);
  line-height: 1;
}

/* 3. BASE DA FICHA: VALOR APOSTADO (ESTILO TÍQUETE OFICIAL) */
.ficha-bet-footer {
  position: relative;
  z-index: 4;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--ficha-bg);
  border: 0.6pt solid var(--ficha-border);
  border-radius: 3px;
  padding: 1mm 2mm;
}

.bet-label-group {
  display: flex;
  align-items: baseline;
  gap: 1mm;
}

.bet-title {
  font-family: var(--font-heading);
  font-size: 5pt;
  font-weight: 900;
  color: var(--ficha-color);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.bet-rs {
  font-family: var(--font-mono);
  font-size: 5.5pt;
  font-weight: 800;
  color: var(--ink-primary);
}

.bet-field-line {
  flex-grow: 1;
  border-bottom: 0.9pt solid var(--ink-primary);
  height: 3.5mm;
  margin-left: 1.8mm;
  min-width: 18mm;
}

/* Variáveis Temáticas por Grupo */
.grupo-1 {
  --ficha-color: var(--g1-color);
  --ficha-bg: var(--g1-bg);
  --ficha-border: var(--g1-border);
}

.grupo-2 {
  --ficha-color: var(--g2-color);
  --ficha-bg: var(--g2-bg);
  --ficha-border: var(--g2-border);
}

.grupo-3 {
  --ficha-color: var(--g3-color);
  --ficha-bg: var(--g3-bg);
  --ficha-border: var(--g3-border);
}

.grupo-4 {
  --ficha-color: var(--g4-color);
  --ficha-bg: var(--g4-bg);
  --ficha-border: var(--g4-border);
}

.grupo-5 {
  --ficha-color: var(--g5-color);
  --ficha-bg: var(--g5-bg);
  --ficha-border: var(--g5-border);
}
"""

# ==============================================================================
# VETORES SVG OFICIAIS DOS 5 ANIMAIS (GAME-ICONS.NET / CC-BY 3.0 & CC0)
# ==============================================================================

# 1. Coelho (Rabbit) — Grupo 01
SVG_SILHOUETTE_COELHO = """<svg viewBox="0 0 512 512"><path d="M242.29 27.29c-4.165 0-4.79.695-5.593 3.058-.803 2.362-.714 8.368 4.065 17.097 8.758 16 32.356 39.726 78.675 64.582 7.15-7.48 15.604-12.92 24.57-16.713-25.48-14.076-44.05-29.58-58.892-42.158-18.93-16.04-31.326-25.867-42.826-25.867zm-66.274 54.66c-3.815.007-4.68.864-5.07 1.355-.39.49-1 1.882-.485 5.125 1.03 6.484 7.16 18.015 18 28.943 21.683 21.855 60.793 42.287 109.542 34.72 2.13-.33 4.725-.616 7.846 1.194 3.12 1.81 4.73 5.96 4.77 8.36.076 4.807-1.495 6.874-2.722 9.546-2.452 5.345-4.35 11.657-4.375 11.47v.003c1.98 15 14.374 26.28 32.396 34.63 18.023 8.353 40.75 13.004 58.875 14.737 12.552 1.2 27.23.995 40.9-1.388-1.555-2.715-2.676-5.576-3.31-8.516-1.763-8.156.105-16.39 4.093-23.327 6.392-11.12 18.112-19.685 32.36-22.83-4.64-7.837-10.434-16.323-17.024-24.592-19.92-24.992-47.433-46.955-67.978-47.384-20.465-.427-44.107 6.055-57.367 24.242-2.24 3.07-5.56 4.144-8.018 4.46-2.457.318-4.623.1-6.92-.284-4.592-.766-9.7-2.373-15.613-4.527-11.825-4.308-26.625-10.89-42.127-17.774-15.502-6.883-31.668-14.06-45.744-19.44-14.076-5.38-26.546-8.735-32.027-8.724zm224.422 61.915a16 16 0 0 1 15.533 15.994 16 16 0 0 1-32 0 16 16 0 0 1 16.467-15.995zM39.79 190.777c-.804.006-2.017.25-4.017 1.24a9 9 0 0 0-.002 0c-4.252 2.103-7.437 7.213-8.883 16.325-1.447 9.11-.696 21.27 1.888 33.53 2.585 12.263 6.954 24.683 12.116 34.634 3.023 5.827 6.386 10.568 9.53 14.133 4.966-17.297 13.943-33.833 27.697-48.44a42.802 42.802 0 0 1-8.365-7.046c-7.05-7.717-11.604-16.873-15.648-24.877-4.045-8.003-7.82-14.854-10.64-17.605-1.408-1.376-2.22-1.714-2.99-1.84a3.888 3.888 0 0 0-.683-.055zm437.63 2.06c-11.655 1.13-21.29 7.89-25.342 14.936-2.183 3.797-2.794 7.368-2.105 10.555.51 2.36 1.71 4.797 4.408 7.29 11.853-4.564 21.157-11.42 26.145-20.938-.286.42.182-1.32-.504-4.184-.494-2.07-1.397-4.71-2.6-7.66zm-198.496 7.724a567.98 567.98 0 0 0-7.3.034c-71.537.806-120.588 13.47-152.624 32.187-36.613 21.393-51.716 50.092-54.844 81.44-3.128 31.346 6.6 65.513 22 94.56 14.84 27.988 35.094 51.027 51.97 62.22H312.19c-.134-1.91-.67-3.555-1.502-5.188-1.637-3.21-4.918-6.56-10.032-9.687-10.228-6.256-27.12-11.045-44.812-14.438-17.693-3.392-36.175-5.596-50.625-8-7.227-1.2-13.393-2.377-18.532-4.125-2.57-.873-4.92-1.813-7.313-3.593-2.392-1.782-5.313-5.385-5.313-9.97 0-2.61 1.27-4.982 2.375-6.22 1.107-1.236 2.03-1.74 2.75-2.124 1.442-.765 2.283-.952 3.125-1.156 1.686-.408 3.238-.605 5.125-.813 3.776-.414 8.714-.75 14.72-1.187 12.01-.875 28.107-2.106 44.968-4.688 33.722-5.162 69.382-16.778 81.156-36.437 6.403-10.69 5.69-20.67-.56-31.156-6.253-10.487-18.818-20.728-35.72-27.376-33.803-13.297-84.07-12.464-132.72 22.47l-10.5-14.627c33.327-23.93 67.99-33.66 99-33.78 18.608-.072 35.892 3.33 50.782 9.187 19.854 7.81 35.666 19.93 44.594 34.906 8.93 14.976 10.196 33.537.563 49.625-17.64 29.45-58.476 39.55-93.876 44.97-5.897.902-11.315 1.47-16.844 2.092 8.423 1.25 17.318 2.606 26.22 4.313 18.544 3.556 36.893 8.25 50.842 16.78 6.975 4.267 12.99 9.656 16.657 16.845 2.058 4.04 3.204 8.593 3.37 13.375h130.66c2.072-1.76 3.435-3.254 3.844-4.063.538-1.064.46-1.178.25-2.062-.423-1.77-3.667-6.165-7.78-11.125-2.527-3.044-11.017-7.917-21.658-10.594-10.64-2.677-23.344-3.65-34.25-2.22l-2.344.283-2.218-.876c-6.667-2.715-11.864-9.652-12.25-16.313-.386-6.66 1.89-12.352 4.72-18.467 5.655-12.23 14.802-26.366 22.186-42.72 7.384-16.352 12.907-34.52 11.72-53.843-1.153-18.73-8.467-38.93-27.84-60.88-.622-.052-1.248-.1-1.86-.16h-.002c-19.505-1.864-43.524-6.62-64.08-16.146-15.233-7.06-29.065-17.167-36.415-31.074-4.692-.1-9.332-.172-13.85-.18z"/></svg>"""

# 2. Elefante (Elephant) — Grupo 02
SVG_SILHOUETTE_ELEFANTE = """<svg viewBox="0 0 512 512"><path d="M236.422 98.393c-126.642-1.276-206.07 46.77-212.058 83.93-2.977 41.18-4.165 83.628-4.016 124.617l4.31 3.796c3.963-15.315 6.47-31.843 14.122-44.085 1.3 27.18 5.068 58.562 11.369 82.067-2.477 24.988-2.118 47.99-3.436 72.978 21.158 12.726 60.485 10.65 67.541 1.986 2.936-20.695 4.981-42.58 3.973-68.535l7.592-35.355c6.418-14.587 25.29-17.243 23.406-31.799l17.828-2.467c.355 25.196-14.375 27.1-24.713 41.653 12.994 5.357 14.676 3.886 24.059 5.124 23.848 2.742 45.234 3.774 67.802-8.175l-3.101-17.541 17.723-3.135 3.064 17.328c4.22 14.097 11.996 104.392 18.559 108.361 13.411 6.417 53.823 6.417 55.472-5.312 1.647-45.786 3.861-90.1-5.07-133.242 3.702-4.1 7.34-8.112 10.928-12.096-20.178-10.157-44.214-25.838-57.62-41.797-9.037-17.21-13.75-38.688-17.304-56.256-2.546-12.943-4.3-26.074-3.81-37.486.244-5.706 1.003-11.018 2.982-15.938 19.848-20.186 56.606-35.68 79.58-46.503-33.273-7.269-71.55 7.386-99.182 17.882zm128.934-9.931c-29.757 10.977-72.215 22.174-92.633 45.267-.807 2.008-1.51 5.563-1.7 9.994-.38 8.863 1.097 21.093 3.487 33.243 2.39 12.15 5.644 24.32 8.41 36.31 4.54 19.67 9.778 39.066 17.828 58.113 7.82 18.502 18.23 36.19 31.815 51.527 2.536 2.863 5.174 5.637 7.914 8.318 10.518-11.597 19.463-24.814 26.684-39.467 6.302-12.788 11.22-26.605 14.54-41.074 3.32-14.47 5.01-29.6 4.97-44.912-.08-30.627-7.2-61.944-18.3-90.89-5.55-14.47-12.56-27.46-23.015-38.426z"/></svg>"""

# 3. Ursinho (Bear) — Grupo 03
SVG_SILHOUETTE_URSINHO = """<svg viewBox="0 0 512 512"><path d="M64.264 44.704c-88.765 25.213-39.73 158.676-2.108 161.887-8.506 42.218-13.32 84.645-12.642 127.824.355 22.67 51.374 58.424 105.35 86.035C186.48 466.787 238.98 466.876 256 467.296c17.02-.42 69.52-.51 101.137-46.846 53.975-27.61 104.994-63.364 105.35-86.035.677-43.179-4.137-85.606-12.643-127.824 37.623-3.211 86.657-136.674-2.108-161.887-28.433 1.462-55.606 16.152-82.172 37.223C317.64 62.233 293.164 61.296 256 61.296c-37.163 0-61.639.937-109.564 20.63-26.566-21.07-53.739-35.76-82.172-37.222zm4.927 49.928c6.057-.096 17.237 5.625 26.809 14.664 3.362 3.175-22.916 51.05-26.818 50.158-4.59-1.05-14.985-48.285-3.725-63.318.745-.994 2.039-1.477 3.734-1.504zm373.618 0c1.695.027 2.99.51 3.734 1.504 11.26 15.033.865 62.268-3.725 63.318-3.902.893-30.18-46.983-26.818-50.158 9.572-9.04 20.752-14.76 26.809-14.664zm-260.85 82.088c17.457-.304 30.686 24.445 42.041 44.576-53.57 15.878-82.575-17.11-57.752-37.777 5.603-4.665 10.823-6.714 15.711-6.8zm148.082 0c4.888.085 10.108 2.134 15.711 6.799 24.823 20.667-4.181 53.655-57.752 37.777 11.355-20.13 24.584-44.88 42.041-44.576zM256 251.548c17.32.223 36.826 9.567 30.197 36.517-1.444 5.872-12.516 8.617-21.197 9.7v8.972c99.884 41.126 79.565 138.559-9 138.559s-108.884-97.433-9-138.559v-8.972c-8.68-1.083-19.753-3.828-21.197-9.7-6.629-26.95 12.877-36.294 30.197-36.517z"/></svg>"""

# 4. Tigre (Tiger) — Grupo 04
SVG_SILHOUETTE_TIGRE = """<svg viewBox="0 0 512 512"><path d="M425.479 25.666c.695.03 1.233.235 1.6.637 28.156 30.856 23.75 58.537 18.36 87.437-2.37 4.836-4.483 8.801-6.79 12.07-5.074 7.188-11.345 12.477-26.674 20.141l8.05 16.098c16.671-8.336 26.4-16.047 33.327-25.86a76.374 76.374 0 0 0 1.99-2.98c23.481 29.638 37.639 65.615 40.162 105.69-10.473-11.076-20.322-14.383-32.865-16.864-3.655-17.373-11.07-34.942-23.44-51.433l-14.398 10.796c22.344 29.793 25.952 62.948 20.375 90.836-5.578 27.889-21.494 49.864-33.201 55.717-17.61 8.805-30.338 21.686-40.338 31.686-5 5-9.353 9.287-12.854 11.965-.175.133-.333.24-.502.365-.852-4.857-2.097-9.886-3.67-15.076-5.313-17.534-14.622-37.068-26.894-57.522l-15.434 9.262c11.728 19.546 20.419 38.012 25.106 53.478 4.687 15.467 4.988 27.718 2.256 34.55-2.733 6.83-7.22 10.423-19.944 10.847-11.082.37-27.763-2.992-49.941-11.604C317.866 378.86 305.89 348.962 304 320c-16 32-32 32-48 32s-32 0-48-32c-1.89 28.962-13.866 58.859 34.24 75.902-22.178 8.612-38.86 11.973-49.941 11.604-12.724-.424-17.211-4.017-19.944-10.848-2.732-6.83-2.43-19.082 2.256-34.549 4.687-15.466 13.378-33.932 25.106-53.478l-15.434-9.262c-12.272 20.454-21.581 39.988-26.894 57.522-1.573 5.19-2.818 10.22-3.67 15.076-.169-.124-.327-.232-.502-.365-3.501-2.678-7.854-6.965-12.854-11.965-10-10-22.728-22.88-40.338-31.686-11.707-5.853-27.623-27.828-33.2-55.717-5.578-27.888-1.97-61.043 20.374-90.836l-14.398-10.796c-12.37 16.491-19.785 34.06-23.44 51.433-12.543 2.48-22.392 5.788-32.865 16.863 2.523-40.074 16.68-76.05 40.162-105.689a76.374 76.374 0 0 0 1.99 2.98c6.927 9.813 16.656 17.524 33.327 25.86l8.05-16.098c-15.329-7.664-21.6-12.953-26.673-20.14-2.308-3.27-4.42-7.235-6.791-12.07-5.39-28.9-9.796-56.582 18.36-87.438.367-.402.905-.607 1.6-.637 9.097-.394 45.217 28.95 79.051 35.594 19.651-6.115 40.847-10.22 63.332-12.094l4.448 15.568c-13.92 1.875-28.343 5.444-44.198 10.729l5.692 17.074c16.147-5.382 30.123-8.91 43.425-10.584l4.463 15.62c-6.012.517-11.858 1.388-17.295 2.667-9.38 2.207-17.681 5.276-23.802 11.397l12.726 12.726c1.88-1.879 7.578-4.81 15.198-6.603 5.387-1.268 11.681-2.114 18.226-2.506L256 144l8.213-28.746c6.545.392 12.839 1.238 18.226 2.506 7.62 1.793 13.319 4.724 15.198 6.603l12.726-12.726c-6.12-6.121-14.422-9.19-23.802-11.397-5.437-1.279-11.283-2.15-17.295-2.668l4.463-15.619c13.302 1.673 27.278 5.202 43.425 10.584l5.692-17.074c-15.855-5.285-30.278-8.854-44.198-10.729l4.448-15.568c22.485 1.873 43.68 5.98 63.332 12.094 33.834-6.643 69.954-35.988 79.05-35.594zm-92.82 109.979c-40 16-59.059 23.357-76.659 23.357-17.6 0-36.658-7.357-76.658-23.357l-6.684 16.71c40 16 60.942 24.643 83.342 24.643s43.342-8.643 83.342-24.643zm43.292 4.33c-14.39 28.78-43.976 43.976-75.976 59.976l7.588 15.172c-4.818 6.521-8.924 14.296-11.934 23.482 0 0-7.629 33.395-8.506 47.916l17.754 2.958C304 272 304 256 312.527 244.664c5.173 7.024 13.406 11.635 22.694 11.635 15.685 0 28.367-13.15 28.367-28.863 0-9.105-4.264-17.342-10.897-22.666 12.317-3.675 24.332-3.772 31.309-3.772v-17.996c-4.717 0-12.708-.032-22.129 1.363 12.116-9.681 22.675-21.335 30.178-36.34zm-239.902 0-16.098 8.05c7.503 15.005 18.062 26.659 30.178 36.34-9.421-1.395-17.412-1.363-22.129-1.363v17.996c6.977 0 18.992.097 31.309 3.772-6.633 5.324-10.897 13.561-10.897 22.666 0 15.712 12.682 28.863 28.367 28.863 9.288 0 17.521-4.611 22.694-11.635C208 256 208 272 207.123 289.48l17.754-2.958c-.877-14.521-8.506-47.916-8.506-47.916-3.01-9.186-7.116-16.96-11.934-23.482l7.588-15.172c-32-16-61.586-31.196-75.976-59.976zm272.488 49.18-17.074 5.69c3.336 10.009 2.55 18.53-.664 27.313-3.214 8.784-9.13 17.608-15.903 26.317-6.773 8.708-14.338 17.246-20.529 26.129-6.19 8.882-11.365 18.396-11.365 29.396h17.996c0-5 2.826-11.486 8.135-19.104 5.309-7.617 12.744-16.08 19.97-25.37 7.227-9.292 14.312-19.468 18.598-31.184 4.287-11.716 5.5-25.196.836-39.188zm-305.074 0c-4.664 13.991-3.45 27.47.836 39.187 4.286 11.716 11.37 21.892 18.597 31.183 7.227 9.292 14.662 17.754 19.971 25.371 5.31 7.618 8.135 14.104 8.135 19.104h17.996c0-11-5.174-20.514-11.365-29.396-6.191-8.883-13.756-17.42-20.53-26.13-6.773-8.708-12.688-17.532-15.902-26.316-3.213-8.784-4-17.304-.664-27.312zm231.758 27.413c5.708 0 10.369 4.638 10.369 10.868 0 6.229-4.66 10.865-10.37 10.865-5.708 0-10.368-4.636-10.368-10.865 0-6.23 4.66-10.868 10.369-10.868zm-158.442 0c5.709 0 10.37 4.638 10.37 10.868 0 6.229-4.661 10.865-10.37 10.865-5.708 0-10.369-4.636-10.369-10.865 0-6.23 4.66-10.868 10.37-10.868zm287.065 12.034C499.508 289.222 495.39 352.61 480 368c-9.787-15.381-20.124-27.816-32-32 9.426 36.059 0 64-16 80 0-16-3.432-23.686-16-32 3.293 39.931-18.232 56.793-32 64-6.028-11.65-17.48-24.433-33.275-35.494a31.768 31.768 0 0 0 5.63-9.164c1.46-3.648 2.367-7.5 2.829-11.526 3.896-1.288 7.36-3.491 10.533-5.918 4.999-3.822 9.646-8.535 14.646-13.535 10-10 21.272-21.12 35.662-28.314 20.293-10.147 36.377-36.172 42.8-68.283 2.935-14.677 3.599-30.76 1.019-47.164zm-415.688 0c-2.58 16.403-1.916 32.487 1.02 47.164 6.422 32.111 22.506 58.136 42.799 68.283 14.39 7.195 25.662 18.314 35.662 28.314 5 5 9.647 9.713 14.646 13.535 3.173 2.427 6.637 4.63 10.533 5.918.462 4.027 1.37 7.878 2.829 11.526a31.768 31.768 0 0 0 5.63 9.164C145.48 423.566 134.028 436.35 128 448c-13.768-7.207-35.293-24.069-32-64-12.568 8.314-16 16-16 32-16-16-25.426-43.941-16-80-11.876 4.184-22.213 16.619-32 32-15.39-15.39-19.508-78.778 16.156-139.398zM424.998 256h-17.996c0 11.5-10.11 26.464-21.834 40.143-5.862 6.839-11.89 13.345-16.754 19.56-4.864 6.215-9.412 11.798-9.412 20.297h17.996c0 .5 1.452-3.918 5.588-9.203 4.136-5.285 10.108-11.779 16.246-18.94 12.276-14.321 26.166-31.358 26.166-51.857zm-320 0H87.002c0 20.5 13.89 37.536 26.166 51.857 6.138 7.161 12.11 13.655 16.246 18.94 4.136 5.285 5.588 9.702 5.588 9.203h17.996c0-8.5-4.548-14.082-9.412-20.297-4.864-6.215-10.892-12.721-16.754-19.56-11.724-13.679-21.834-28.642-21.834-40.143zm201.725 168.805c4.823.6 9.34.83 13.576.69a53.604 53.604 0 0 0 5.383-.466c-2.526 8.899-6.629 17.366-12.768 24.733C301.151 463.877 282 472.998 256 472.998s-45.151-9.12-56.914-23.236c-6.14-7.367-10.242-15.834-12.768-24.733 1.752.236 3.54.404 5.383.465 4.236.141 8.753-.088 13.576-.69 1.86 4.965 4.373 9.518 7.637 13.434 8.237 9.885 21.086 16.764 43.086 16.764s34.849-6.88 43.086-16.764c3.264-3.916 5.776-8.47 7.637-13.433z"/></svg>"""

# 5. Cão (Hound / Dog) — Grupo 05
SVG_SILHOUETTE_CAO = """<svg viewBox="0 0 512 512"><path d="m137.75 17.28-15.313 78.782 20.313 56.876h45.97L137.75 17.28zM74.5 19 20 378.156v116.156h208L210.125 386.5H113.28l-2.218-6.156-25.78-71.594 17.562-6.344 23.562 65.406h90.344l230.688-2.968 9.812-33.406H278.5V312.75h184.22l7.374-25.156L415.53 209.5H291.47l-20.345-37.594h-75.28l-.095-.28h-46.313L159.563 200l-17.593 6.28-26.532-74.25-.126.72L74.5 19zm133.375 178.22h56.094l21.405 38.874-26.094-.438-51.405-38.437zm230.47 12.28 38.53 55.094L493.03 209.5h-54.686zm-82.814 15.938c6.613 0 11.97 5.356 11.97 11.968 0 6.613-5.357 11.97-11.97 11.97-6.61 0-11.967-5.357-11.967-11.97 0-6.612 5.356-11.97 11.968-11.97zm44.595 0c6.612 0 12 5.356 12 11.968 0 6.613-5.388 11.97-12 11.97s-11.97-5.357-11.97-11.97c0-6.612 5.358-11.97 11.97-11.97zm-66.188 29.187c6.612 0 11.97 5.356 11.97 11.97 0 6.61-5.358 11.967-11.97 11.967-6.61 0-11.968-5.356-11.968-11.968 0-6.613 5.356-11.97 11.967-11.97zm43.125 0c6.612 0 12 5.356 12 11.97 0 6.61-5.388 11.967-12 11.967-6.61 0-11.968-5.356-11.968-11.968 0-6.613 5.357-11.97 11.97-11.97zm42.063 0c6.612 0 11.97 5.356 11.97 11.97 0 6.61-5.358 11.967-11.97 11.967-6.612 0-11.97-5.356-11.97-11.968 0-6.613 5.358-11.97 11.97-11.97z"/></svg>"""




# Textura Geométrica de Segurança para Fichas de Aposta
SVG_TEXTURE_FICHA = """<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="token-mesh" width="12" height="12" patternUnits="userSpaceOnUse">
      <circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" stroke-width="0.5"/>
      <circle cx="6" cy="6" r="2.2" fill="none" stroke="currentColor" stroke-width="0.35"/>
      <path d="M0,6 L12,6 M6,0 L6,12" stroke="currentColor" stroke-width="0.3" stroke-dasharray="1 1"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#token-mesh)"/>
</svg>"""

DADOS_GRUPOS = [
    {
        "id": 1,
        "classe": "grupo-1",
        "nome": "Grupo 01",
        "animal": "Coelho",
        "svg_silhueta": SVG_SILHOUETTE_COELHO
    },
    {
        "id": 2,
        "classe": "grupo-2",
        "nome": "Grupo 02",
        "animal": "Elefante",
        "svg_silhueta": SVG_SILHOUETTE_ELEFANTE
    },
    {
        "id": 3,
        "classe": "grupo-3",
        "nome": "Grupo 03",
        "animal": "Ursinho",
        "svg_silhueta": SVG_SILHOUETTE_URSINHO
    },
    {
        "id": 4,
        "classe": "grupo-4",
        "nome": "Grupo 04",
        "animal": "Tigre",
        "svg_silhueta": SVG_SILHOUETTE_TIGRE
    },
    {
        "id": 5,
        "classe": "grupo-5",
        "nome": "Grupo 05",
        "animal": "Cão",
        "svg_silhueta": SVG_SILHOUETTE_CAO
    }
]

# Diagramas Científicos das Cédulas
SVG_DIAGRAMA_100 = """
<svg viewBox="0 0 80 44" fill="none" stroke="currentColor" stroke-width="1.1">
  <circle cx="40" cy="22" r="3" fill="currentColor"/>
  <ellipse cx="40" cy="22" rx="28" ry="9" stroke-dasharray="2.5 1.5" stroke-width="0.8"/>
  <ellipse cx="40" cy="22" rx="9" ry="17" stroke-dasharray="2.5 1.5" stroke-width="0.8"/>
  <ellipse cx="40" cy="22" rx="24" ry="13" transform="rotate(45 40 22)" stroke-width="1.1"/>
  <ellipse cx="40" cy="22" rx="24" ry="13" transform="rotate(-45 40 22)" stroke-width="1.1"/>
  <circle cx="23" cy="11" r="1.6" fill="currentColor"/>
  <circle cx="57" cy="33" r="1.6" fill="currentColor"/>
</svg>
"""

SVG_DIAGRAMA_50 = """
<svg viewBox="0 0 80 44" fill="none" stroke="currentColor" stroke-width="1.1">
  <!-- Eixos Coordenados -->
  <path d="M 12 36 L 72 36 M 12 36 L 12 8" stroke-width="0.8" stroke-opacity="0.6"/>
  <!-- Curva de Energia de Ativação -->
  <path d="M 14 28 C 26 28, 28 10, 38 10 C 48 10, 52 32, 70 32" stroke-width="1.4"/>
  <!-- Barreira Catalisada (tracejada) -->
  <path d="M 14 28 C 26 28, 30 18, 38 18 C 46 18, 52 32, 70 32" stroke-dasharray="2 1.5" stroke-width="0.9" stroke-opacity="0.75"/>
  <!-- Ponto de Transição Ea -->
  <circle cx="38" cy="10" r="1.8" fill="currentColor"/>
</svg>
"""

SVG_DIAGRAMA_10 = """
<svg viewBox="0 0 80 44" fill="none" stroke="currentColor" stroke-width="1.1">
  <!-- Retículo / Ligações Moleculares Covalentes -->
  <polygon points="40,8 60,19 60,33 40,40 20,33 20,19" stroke-width="1.2"/>
  <line x1="40" y1="8" x2="40" y2="40" stroke-width="0.8" stroke-dasharray="2 1.5"/>
  <line x1="20" y1="19" x2="60" y2="33" stroke-width="0.8" stroke-dasharray="2 1.5"/>
  <line x1="20" y1="33" x2="60" y2="19" stroke-width="0.8" stroke-dasharray="2 1.5"/>
  <!-- Átomos nos Vértices -->
  <circle cx="40" cy="8" r="2.2" fill="currentColor"/>
  <circle cx="60" cy="19" r="2.2" fill="currentColor"/>
  <circle cx="60" cy="33" r="2.2" fill="currentColor"/>
  <circle cx="40" cy="40" r="2.2" fill="currentColor"/>
  <circle cx="20" cy="33" r="2.2" fill="currentColor"/>
  <circle cx="20" cy="19" r="2.2" fill="currentColor"/>
</svg>
"""

# Onda Holográfica Kinegram
SVG_WAVE_HOLO = """
<svg viewBox="0 0 16 48" fill="none" stroke="currentColor" stroke-width="0.9">
  <path d="M8 0 Q14 8 8 16 T8 32 T8 48"/>
  <path d="M4 0 Q10 8 4 16 T4 32 T4 48" stroke-opacity="0.4"/>
  <path d="M12 0 Q18 8 12 16 T12 32 T12 48" stroke-opacity="0.4"/>
</svg>
"""

# ==============================================================================
# GERADORES DE HTML
# ==============================================================================

def gerar_crop_marks_html():
    """Gera o HTML das guias de corte externas milimétricas."""
    return """
        <!-- Guias Verticais de Corte (Topo e Base) -->
        <div class="crop-mark crop-v crop-v-top-0"></div>
        <div class="crop-mark crop-v crop-v-top-1"></div>
        <div class="crop-mark crop-v crop-v-top-2"></div>
        <div class="crop-mark crop-v crop-v-top-3"></div>

        <div class="crop-mark crop-v crop-v-bot-0"></div>
        <div class="crop-mark crop-v crop-v-bot-1"></div>
        <div class="crop-mark crop-v crop-v-bot-2"></div>
        <div class="crop-mark crop-v crop-v-bot-3"></div>

        <!-- Guias Horizontais de Corte (Esquerda e Direita) -->
        <div class="crop-mark crop-h crop-h-l-0"></div>
        <div class="crop-mark crop-h crop-h-l-1"></div>
        <div class="crop-mark crop-h crop-h-l-2"></div>
        <div class="crop-mark crop-h crop-h-l-3"></div>
        <div class="crop-mark crop-h crop-h-l-4"></div>
        <div class="crop-mark crop-h crop-h-l-5"></div>
        <div class="crop-mark crop-h crop-h-l-6"></div>

        <div class="crop-mark crop-h crop-h-r-0"></div>
        <div class="crop-mark crop-h crop-h-r-1"></div>
        <div class="crop-mark crop-h crop-h-r-2"></div>
        <div class="crop-mark crop-h crop-h-r-3"></div>
        <div class="crop-mark crop-h crop-h-r-4"></div>
        <div class="crop-mark crop-h crop-h-r-5"></div>
        <div class="crop-mark crop-h crop-h-r-6"></div>
    """

def render_cedula_html(valor, kit_num, serial_num):
    """Renderiza uma cédula individual de 63mm x 45mm."""
    if valor == 100:
        cls_tema = "card-100"
        txt_extenso = "CEM REAIS"
        sci_svg = SVG_DIAGRAMA_100
        sci_tag = "ORBITAIS & ONDAS (R$ 100)"
        micro_txt = "PSI·WAVE·1S2·2S2·2P6"
        signer = "Lavoisier"
        signer_cargo = "Pai da Química"
    elif valor == 50:
        cls_tema = "card-50"
        txt_extenso = "CINQUENTA REAIS"
        sci_svg = SVG_DIAGRAMA_50
        sci_tag = "CINÉTICA & TERMO (ΔG < 0)"
        micro_txt = "DELTA·G·DELTA·H·TERMO"
        signer = "Gibbs"
        signer_cargo = "Termodinâmica"
    else: # 10
        cls_tema = "card-10"
        txt_extenso = "DEZ REAIS"
        sci_svg = SVG_DIAGRAMA_10
        sci_tag = "LIGAÇÕES & RETÍCULO (R$ 10)"
        micro_txt = "OCTET·LEWIS·BOND·10"
        signer = "Pauling"
        signer_cargo = "Eletronegatividade"

    serial_str = f"№ BR-{valor:03d}-{serial_num:04d}"
    kit_str = f"KIT {kit_num:02d}"

    return f"""
    <div class="money-card {cls_tema}">
        <!-- ZONA 1: SEGURANÇA KINEGRAM (12mm) -->
        <div class="money-sec">
            <div class="sec-val-top">{valor}</div>
            <div class="sec-wave">
                {SVG_WAVE_HOLO}
            </div>
            <div class="sec-micro">{micro_txt}</div>
            <div class="sec-val-bot">{valor}</div>
        </div>

        <!-- ZONA 2: CORPO CIENTÍFICO (51mm) -->
        <div class="money-body">
            <div class="money-header">
                <span class="inst-title">ALL-IN QUÍMICO • BANCO</span>
                <span class="kit-badge">{kit_str}</span>
            </div>

            <div class="money-mid">
                <div class="sci-diagram-box">
                    {sci_svg}
                    <div class="sci-tag">{sci_tag}</div>
                </div>
                <div class="money-val-group">
                    <div><span class="val-currency">R$</span><span class="val-big">{valor}</span></div>
                    <div class="val-extenso">{txt_extenso}</div>
                </div>
            </div>

            <div class="money-footer">
                <span class="serial-code">{serial_str}</span>
                <div class="signer-box">
                    <span class="signer-sig">{signer}</span>
                    <span class="signer-title">{signer_cargo}</span>
                </div>
            </div>
        </div>
    </div>
    """

def render_ficha_aposta_html(grupo, numero_pergunta=None):
    """Renderiza uma ficha de aposta individual de 63mm x 45mm."""
    pergunta_box = f'<span class="round-line"></span>'
    if numero_pergunta is not None:
        pergunta_box = f'<span style="font-family: var(--font-heading); font-weight: 800; font-size: 5.5pt; color: var(--ink-primary); padding-left: 1mm;">{numero_pergunta:02d}</span>'

    return f"""
    <div class="ficha-card {grupo['classe']}">
        <!-- TEXTURA GEOMÉTRICA DE SEGURANÇA -->
        <div class="ficha-texture-bg">
            {SVG_TEXTURE_FICHA}
        </div>

        <!-- MEDALHÃO / SILHUETA OFICIAL DO ANIMAL -->
        <div class="ficha-silhouette-bg">
            {grupo['svg_silhueta']}
        </div>

        <!-- 1. CABEÇALHO DA FICHA -->
        <div class="ficha-header">
            <div class="ficha-group-badge">
                <div class="ficha-group-icon">
                    {grupo['svg_silhueta']}
                </div>
                <div class="ficha-group-text">
                    <span class="ficha-group-name">{grupo['nome']}</span>
                    <span class="ficha-group-animal">{grupo['animal']}</span>
                </div>
            </div>
            <div class="ficha-round-box">
                <span class="round-label">RODADA:</span>
                {pergunta_box}
            </div>
        </div>

        <!-- 2. SELEÇÃO DE ALTERNATIVA CONVENCIONAL [ A ] OU [ B ] -->
        <div class="ficha-choices-section">
            <span class="choices-prompt">ALTERNATIVA ESCOLHIDA</span>
            <div class="choices-container">
                <div class="choice-box">
                    <span class="choice-circle"></span>
                    <span class="choice-letter">A</span>
                </div>
                <div class="choice-box">
                    <span class="choice-circle"></span>
                    <span class="choice-letter">B</span>
                </div>
            </div>
        </div>

        <!-- 3. BASE DA FICHA: VALOR APOSTADO -->
        <div class="ficha-bet-footer">
            <div class="bet-label-group">
                <span class="bet-title">APOSTA:</span>
                <span class="bet-rs">R$</span>
            </div>
            <div class="bet-field-line"></div>
        </div>
    </div>
    """

def criar_pagina_a4(itens_html, rodape_esq="", rodape_dir=""):
    """Empacota exatamente 18 itens em uma página A4 padronizada com crop marks."""
    return f"""
    <div class="page">
        {gerar_crop_marks_html()}
        <div class="grid-sheet">
            {"".join(itens_html)}
        </div>
        <div class="page-footer-label">
            <span>{rodape_esq}</span>
            <span>PADRÃO CORTE 63×45mm • {rodape_dir}</span>
        </div>
    </div>
    """

def empacotar_documento_html(titulo, desc_painel, paginas_html, extra_css=""):
    """Gera o documento HTML completo e funcional para impressão."""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        {CSS_PRINT_CORE}
        {CSS_CEDULAS}
        {CSS_FICHAS}
        {extra_css}
    </style>
</head>
<body>
    <div class="no-print-bar">
        <h1>{titulo}</h1>
        <p>{desc_painel}</p>
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir / Salvar como PDF (A4)</button>
    </div>

    {"".join(paginas_html)}
</body>
</html>
"""

# ==============================================================================
# MODOS DE PRODUÇÃO: CÉDULAS
# ==============================================================================

def gerar_amostra_cedulas(caminho="amostra_cedulas_teste.html"):
    """Gera 1 página A4 com 18 cédulas de teste (6 de R$ 100, 6 de R$ 50, 6 de R$ 10)."""
    itens = []
    # 6 notas de 100
    for i in range(1, 7):
        itens.append(render_cedula_html(100, 1, i))
    # 6 notas de 50
    for i in range(1, 7):
        itens.append(render_cedula_html(50, 1, i))
    # 6 notas de 10
    for i in range(1, 7):
        itens.append(render_cedula_html(10, 1, i))

    pagina = criar_pagina_a4(
        itens,
        rodape_esq="AMOSTRA DE AUDITORIA • 6x R$ 100 + 6x R$ 50 + 6x R$ 10 = R$ 960",
        rodape_dir="FOLHA DE TESTE 01/01"
    )

    doc = empacotar_documento_html(
        titulo="All-In Químico — Folha de Amostra de Cédulas (63×45mm)",
        desc_painel="Folha de auditoria para conferência de corte e impressão. Contém 18 cédulas (6× R$ 100, 6× R$ 50, 6× R$ 10 = R$ 960).",
        paginas_html=[pagina]
    )

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  [OK] Folha de Amostra de Cédulas gerada: '{caminho}' (1 página, 18 cédulas)")

def gerar_cedulas_por_tipo(valor, total_notas, nome_arquivo):
    """Gera um arquivo HTML específico para uma denominação de cédula."""
    notas_por_folha = 18
    num_folhas = math.ceil(total_notas / notas_por_folha)
    paginas = []
    serial_idx = 1

    for folha in range(1, num_folhas + 1):
        itens = []
        for slot in range(notas_por_folha):
            if serial_idx <= total_notas:
                kit_num = ((serial_idx - 1) // 6) + 1 if valor != 10 else ((serial_idx - 1) // 10) + 1
                itens.append(render_cedula_html(valor, kit_num, serial_idx))
                serial_idx += 1
            else:
                # Preenchimento reserva
                itens.append(render_cedula_html(valor, 99, 9000 + slot))

        paginas.append(criar_pagina_a4(
            itens,
            rodape_esq=f"CÉDULAS R$ {valor} • TOTAL: {total_notas} NOTAS (R$ {total_notas * valor:,.2f})",
            rodape_dir=f"FOLHA {folha:02d}/{num_folhas:02d}"
        ))

    doc = empacotar_documento_html(
        titulo=f"All-In Químico — Cédulas de R$ {valor} ({total_notas} notas = R$ {total_notas * valor:,.2f})",
        desc_painel=f"Arquivo exclusivo das cédulas de <strong>R$ {valor}</strong>. Total de <strong>{total_notas} notas</strong> distribuídas em <strong>{num_folhas} folhas A4</strong>.",
        paginas_html=paginas
    )

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  [OK] Cédulas R$ {valor} geradas: '{nome_arquivo}' ({num_folhas} folhas A4, {total_notas} cédulas = R$ {total_notas*valor})")

def gerar_lote_completo_10000():
    """
    Gera os 10 Kits = R$ 10.000 em 3 arquivos separados:
      - cedulas_100_reais.html: 60 cédulas (4 folhas A4, R$ 6.000)
      - cedulas_50_reais.html:  60 cédulas (4 folhas A4, R$ 3.000)
      - cedulas_10_reais.html:  100 cédulas (6 folhas A4, R$ 1.000)
    """
    print("\n--- GERANDO ARQUIVOS SEPARADOS DAS CÉDULAS (TOTAL R$ 10.000) ---")
    gerar_cedulas_por_tipo(100, 60, "cedulas_100_reais.html")
    gerar_cedulas_por_tipo(50, 60, "cedulas_50_reais.html")
    gerar_cedulas_por_tipo(10, 100, "cedulas_10_reais.html")
    print("  => Total em jogo: R$ 6.000 + R$ 3.000 + R$ 1.000 = R$ 10.000,00 gerados com sucesso!\n")

# ==============================================================================
# MODOS DE PRODUÇÃO: FICHAS DE APOSTA
# ==============================================================================

def gerar_amostra_fichas(caminho="amostra_fichas_teste.html"):
    """Gera 1 folha A4 com amostras de fichas de todos os 5 grupos."""
    itens = []
    # 3 fichas para cada um dos 5 grupos (15) + 3 fichas extras
    for grupo in DADOS_GRUPOS:
        for i in range(1, 4):
            itens.append(render_ficha_aposta_html(grupo, numero_pergunta=i))
    # 3 fichas bônus
    itens.append(render_ficha_aposta_html(DADOS_GRUPOS[0], numero_pergunta=4))
    itens.append(render_ficha_aposta_html(DADOS_GRUPOS[1], numero_pergunta=4))
    itens.append(render_ficha_aposta_html(DADOS_GRUPOS[2], numero_pergunta=4))

    pagina = criar_pagina_a4(
        itens,
        rodape_esq="AMOSTRA DE AUDITORIA • FICHAS DE APOSTA DE TODOS OS 5 GRUPOS",
        rodape_dir="FOLHA DE TESTE 01/01"
    )

    doc = empacotar_documento_html(
        titulo="All-In Químico — Folha de Amostra de Fichas de Aposta (63×45mm)",
        desc_painel="Folha de auditoria contendo fichas de teste de todas as 5 equipes (Coelho, Elefante, Ursinho, Tigre e Cão) com caixas [ A ] e [ B ].",
        paginas_html=[pagina]
    )

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  [OK] Folha de Amostra de Fichas gerada: '{caminho}' (1 página, 18 fichas)")

def gerar_fichas_grupo_individual(grupo, caminho):
    """Gera 1 folha A4 completa com 18 fichas para uma equipe específica."""
    itens = []
    for i in range(1, 19):
        itens.append(render_ficha_aposta_html(grupo, numero_pergunta=i))

    pagina = criar_pagina_a4(
        itens,
        rodape_esq=f"FICHAS DE APOSTA OFICIAIS • {grupo['nome'].upper()} — {grupo['animal'].upper()}",
        rodape_dir="18 FICHAS • FOLHA 01/01"
    )

    doc = empacotar_documento_html(
        titulo=f"All-In Químico — Fichas de Aposta: {grupo['nome']} ({grupo['animal']})",
        desc_painel=f"Folha com <strong>18 fichas de aposta</strong> exclusivas para o <strong>{grupo['nome']} ({grupo['animal']})</strong>. Marcação [ A ] ou [ B ] e valor apostado.",
        paginas_html=[pagina]
    )

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  [OK] Fichas do {grupo['nome']} ({grupo['animal']}) geradas: '{caminho}' (1 folha A4, 18 fichas)")

def gerar_todas_fichas_aposta():
    """
    Gera arquivos separados para cada um dos 5 grupos + 1 arquivo consolidado
    com as 5 folhas A4 unificadas (90 fichas no total).
    """
    print("\n--- GERANDO FICHAS DE APOSTA PARA OS 5 GRUPOS ---")
    nomes_arquivos = [
        "fichas_grupo1_coelho.html",
        "fichas_grupo2_elefante.html",
        "fichas_grupo3_ursinho.html",
        "fichas_grupo4_tigre.html",
        "fichas_grupo5_cao.html"
    ]

    paginas_unificadas = []

    for i, grupo in enumerate(DADOS_GRUPOS):
        gerar_fichas_grupo_individual(grupo, nomes_arquivos[i])

        # Cria itens para o arquivo unificado
        itens_equipe = [render_ficha_aposta_html(grupo, numero_pergunta=n) for n in range(1, 19)]
        paginas_unificadas.append(criar_pagina_a4(
            itens_equipe,
            rodape_esq=f"FICHAS DE APOSTA • {grupo['nome'].upper()} — {grupo['animal'].upper()}",
            rodape_dir=f"FOLHA {i+1:02d}/05"
        ))

    # Arquivo consolidado com todas as 5 folhas
    doc_unificado = empacotar_documento_html(
        titulo="All-In Químico — Fichas de Aposta de Todas as Equipes (5 Grupos)",
        desc_painel="Conjunto completo de <strong>5 folhas A4 (90 fichas)</strong> com 18 fichas dedicadas para cada uma das 5 equipes.",
        paginas_html=paginas_unificadas
    )

    with open("fichas_todas_equipes.html", "w", encoding="utf-8") as f:
        f.write(doc_unificado)
    print("  [OK] Arquivo unificado de fichas gerado: 'fichas_todas_equipes.html' (5 folhas A4, 90 fichas)\n")

# ==============================================================================
# MENU INTERATIVO E CLI
# ==============================================================================

def menu_interativo():
    while True:
        print("\n" + "=" * 65)
        print("    ALL-IN QUÍMICO — GERADOR DE MATERIAIS DE MESA (63×45mm)")
        print("=" * 65)
        print("  [1] CÉDULAS: Gerar Folha de Amostra de Teste (18 cédulas)")
        print("  [2] CÉDULAS: Gerar Lote Completo de R$ 10.000 (Arquivos Separados)")
        print("  [3] FICHAS:  Gerar Folha de Amostra de Teste (Todos os Bichos)")
        print("  [4] FICHAS:  Gerar Fichas Oficiais das 5 Equipes (5 Folhas A4)")
        print("  [5] TUDO:    Gerar Todos os Materiais (Amostras + Lote Completo)")
        print("  [0] Sair")
        print("-" * 65)
        
        try:
            escolha = input("Selecione uma opção [0-5]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            break

        if escolha == "1":
            gerar_amostra_cedulas()
        elif escolha == "2":
            gerar_lote_completo_10000()
        elif escolha == "3":
            gerar_amostra_fichas()
        elif escolha == "4":
            gerar_todas_fichas_aposta()
        elif escolha == "5":
            gerar_amostra_cedulas()
            gerar_lote_completo_10000()
            gerar_amostra_fichas()
            gerar_todas_fichas_aposta()
            print(">>> Todos os materiais foram gerados com sucesso no diretório de trabalho!")
        elif escolha == "0":
            print("Encerrando gerador. Bons jogos!")
            break
        else:
            print("Opção inválida! Digite um número de 0 a 5.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--tudo", "-a", "--all"]:
            gerar_amostra_cedulas()
            gerar_lote_completo_10000()
            gerar_amostra_fichas()
            gerar_todas_fichas_aposta()
        elif arg in ["--cedulas-amostra"]:
            gerar_amostra_cedulas()
        elif arg in ["--cedulas-total", "--cedulas"]:
            gerar_lote_completo_10000()
        elif arg in ["--fichas-amostra"]:
            gerar_amostra_fichas()
        elif arg in ["--fichas", "--fichas-todas"]:
            gerar_todas_fichas_aposta()
        else:
            print(f"Argumento não reconhecido: {arg}")
            print("Uso: python gerar_materiais_all_in.py [--tudo | --cedulas-amostra | --cedulas-total | --fichas-amostra | --fichas-todas]")
    else:
        menu_interativo()
