"use strict";
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const money = PyNDSCalculator;
const rowsContainer = $("#rows");
const vatRateInput = $("#vatRate");
const settingsStatus = $("#settingsStatus");
const MAX_ROWS = 1000;
let backend = null;
let saveTimer = null;
let loadingSettings = true;
const settingFields = {
  vatRate: "vatRate", appendix_no: "appendixNo", supply_contract_line: "supplyContractLine",
  spec_line: "specLine", contract_line: "contractLine", spec_date: "specDate",
  buyer_position: "buyerPosition", seller_position: "sellerPosition", buyer_org: "buyerOrg",
  seller_org: "sellerOrg", buyer_sign: "buyerSign", seller_sign: "sellerSign",
};
const setStatus = (text, error = false) => {
  settingsStatus.textContent = text;
  settingsStatus.classList.toggle("is-error", error);
};
const collectSettings = () => ({
  ...Object.fromEntries(Object.entries(settingFields).map(([key, id]) => [key, $(`#${id}`).value.trim()])),
  detail_rows: $$("[data-detail-label]").map(row => [row.dataset.detailLabel, $("textarea", row).value.trim()]),
});
const applySettings = (settings) => {
  for (const [key, id] of Object.entries(settingFields)) {
    if (settings[key] !== undefined) $(`#${id}`).value = settings[key];
  }
  const values = new Map(settings.detail_rows || []);
  $$("[data-detail-label]").forEach(row => {
    $("textarea", row).value = values.get(row.dataset.detailLabel) || "";
  });
  refreshAll();
};
const saveSettings = () => {
  clearTimeout(saveTimer);
  if (loadingSettings || !backend) return;
  try { money.scaled(vatRateInput.value, 2, 100, 2200n); }
  catch (error) { setStatus(error.message, true); return; }
  backend.saveSettings(JSON.stringify(collectSettings()));
};
const scheduleSettingsSave = () => {
  if (loadingSettings) return;
  if (!backend) { setStatus("Настройки браузерного демо действуют до перезагрузки страницы."); return; }
  clearTimeout(saveTimer);
  setStatus("Автосохранение…");
  saveTimer = setTimeout(saveSettings, 600);
};
const readRow = row => Object.fromEntries(
  ["name", "gross", "net", "qty", "unit", "gost"].map(key => [key, $(`.field--${key}`, row).value.trim()])
);
const collectRows = () => $$(".table__row", rowsContainer).map(row => ({...readRow(row), source: row.dataset.source || "gross"}))
  .filter(row => row.name || row.gross || row.net);
const getPayload = () => ({vatRate: vatRateInput.value, rows: collectRows(), settings: collectSettings()});
const refreshRow = row => {
  const raw = readRow(row);
  const source = row.dataset.source || "gross";
  const opposite = source === "gross" ? "net" : "gross";
  row.classList.remove("has-error");
  $(".row-error", row).textContent = "";
  row.result = null;
  if (!raw[source]) {
    $(`.field--${opposite}`, row).value = "";
    $(".field--vat", row).value = "";
    return;
  }
  try {
    const result = money.calculate({...raw, source}, vatRateInput.value);
    $(`.field--${opposite}`, row).value = money.format(result[opposite]);
    $(".field--vat", row).value = money.format(result.vat);
    row.result = result;
  } catch (error) {
    row.classList.add("has-error");
    $(".row-error", row).textContent = error.message;
    $(`.field--${opposite}`, row).value = "";
    $(".field--vat", row).value = "";
  }
};
const updateTotals = () => {
  const rows = $$(".table__row", rowsContainer);
  const totals = rows.reduce((sum, row) => {
    if (row.result) for (const key of ["sumNet", "sumGross", "sumVat"]) sum[key] += row.result[key];
    return sum;
  }, {sumNet: 0n, sumGross: 0n, sumVat: 0n});
  for (const [key, value] of Object.entries(totals)) $(`#${key}`).textContent = `${money.format(value)} ₽`;
  $("#positionCount").textContent = String(collectRows().length);
  $("#tableStatus").textContent = rows.some(row => row.classList.contains("has-error"))
    ? "Исправьте отмеченные строки: они не включены в итоги." : "Итоги учитывают количество. Сохраните таблицу в Excel перед закрытием.";
};
const refreshAll = () => {
  try {
    $("#vatRateBadge").textContent = `${money.format(money.scaled(vatRateInput.value, 2, 100, 2200n))}%`;
    vatRateInput.setAttribute("aria-invalid", "false");
  } catch (error) {
    $("#vatRateBadge").textContent = "Проверьте ставку";
    vatRateInput.setAttribute("aria-invalid", "true");
  }
  $$(".table__row", rowsContainer).forEach(refreshRow);
  updateTotals();
};
const reindexRows = () => {
  $$(".table__row", rowsContainer).forEach((row, index) => {
    $(".cell--index", row).textContent = index + 1;
    $$("input", row).forEach(input => input.setAttribute("aria-label", `${input.dataset.label}, строка ${index + 1}`));
    $(".button--danger", row).setAttribute("aria-label", `Удалить строку ${index + 1}`);
  });
  updateTotals();
};
const createRow = (data = {}) => {
  const row = document.createElement("div");
  row.className = "table__row";
  row.innerHTML = `
    <div class="cell cell--index" data-label="№"></div>
    <div class="cell cell--product" data-label="Наименование товара">
      <input class="field field--name" data-label="Наименование" placeholder="Наименование товара" maxlength="500">
      <div class="row-details">
        <label>Кол-во<input class="field field--qty" data-label="Количество" inputmode="decimal" value="1"></label>
        <label>Ед. изм.<input class="field field--unit" data-label="Единица измерения" value="шт" maxlength="30"></label>
        <label>ГОСТ / ТУ<input class="field field--gost" data-label="ГОСТ или ТУ" placeholder="—" maxlength="100"></label>
      </div>
      <div class="row-error" role="status"></div>
    </div>
    <div class="cell" data-label="Цена с НДС"><input class="field field--gross" data-label="Цена с НДС" inputmode="decimal" placeholder="0,00"></div>
    <div class="cell" data-label="Цена без НДС"><input class="field field--net" data-label="Цена без НДС" inputmode="decimal" placeholder="0,00"></div>
    <div class="cell" data-label="НДС за ед."><input class="field field--vat" data-label="НДС за единицу" readonly tabindex="-1"></div>
    <div class="cell cell--action"><button class="button button--danger" type="button">×</button></div>`;
  for (const key of ["name", "gross", "net", "qty", "unit", "gost"]) {
    if (data[key] !== undefined && data[key] !== "") $(`.field--${key}`, row).value = data[key];
  }
  row.dataset.source = data.source || (data.gross !== undefined && data.gross !== "" ? "gross" : data.net ? "net" : "gross");
  row.addEventListener("input", event => {
    for (const key of ["net", "gross"]) if (event.target.classList.contains(`field--${key}`)) row.dataset.source = key;
    refreshRow(row);
    updateTotals();
  });
  row.addEventListener("focusout", event => {
    const key = row.dataset.source;
    if (event.target.classList.contains(`field--${key}`) && row.result) event.target.value = money.format(row.result[key]);
  });
  $(".button--danger", row).addEventListener("click", () => { row.remove(); reindexRows(); });
  rowsContainer.appendChild(row);
  refreshRow(row);
  if (row.result) {
    $(`.field--${row.dataset.source}`, row).value = money.format(row.result[row.dataset.source]);
    $(".field--qty", row).value = money.decimal(row.result.qty, 3).replace(/0+$/, "").replace(/\.$/, "").replace(".", ",");
  }
  return row;
};
const addRows = (count = 1) => {
  const available = MAX_ROWS - rowsContainer.children.length;
  const total = Math.min(count, available);
  if (count > available) window.alert(`В таблице может быть не более ${MAX_ROWS} строк.`);
  for (let index = 0; index < total; index++) createRow();
  reindexRows();
};
const confirmReplace = () => !collectRows().length || window.confirm("Заменить текущую таблицу? Несохранённые строки будут потеряны.");
const replaceRows = rows => {
  rowsContainer.replaceChildren();
  rows.slice(0, MAX_ROWS).forEach(createRow);
  reindexRows();
};
const importRows = payload => {
  try {
    const data = JSON.parse(payload);
    if (!Array.isArray(data.rows) || !data.rows.length) throw new Error("В файле нет товарных строк.");
    if (confirmReplace()) replaceRows(data.rows);
  } catch (error) { window.alert(error.message); }
};
const requestExport = method => {
  const payload = getPayload();
  if (!payload.rows.length) { window.alert("Нет данных для экспорта."); return; }
  if (vatRateInput.getAttribute("aria-invalid") === "true") { window.alert("Проверьте ставку НДС."); return; }
  if ($(".has-error", rowsContainer) || payload.rows.some(row => !row.name || (!row.gross && !row.net))) {
    window.alert("Проверьте наименования, цены и количество во всех строках."); return;
  }
  const total = $$(".table__row", rowsContainer).reduce((sum, row) => sum + (row.result?.sumGross || 0n), 0n);
  if (total > 100000000000000n) { window.alert("Общая сумма с НДС не должна превышать 1 000 000 000 000 рублей."); return; }
  if (backend) backend[method](JSON.stringify(payload));
};
const activateTab = name => {
  $$(".tab").forEach(button => {
    const active = button.dataset.tab === name;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  $$("[data-tab-panel]").forEach(panel => panel.classList.toggle("is-hidden", panel.dataset.tabPanel !== name));
};
$$(".tab").forEach(button => button.addEventListener("click", () => activateTab(button.dataset.tab)));
$("#addRow").addEventListener("click", () => { addRows(); $(".field--name", rowsContainer.lastElementChild)?.focus(); });
$("#addRows").addEventListener("click", () => {
  const count = Number($("#rowCount").value);
  if (!Number.isInteger(count) || count < 1 || count > MAX_ROWS) { window.alert("Введите количество строк от 1 до 1000."); return; }
  addRows(count);
});
$("#clearRows").addEventListener("click", () => { if (confirmReplace()) { replaceRows([]); addRows(); } });
$("#loadDemo").addEventListener("click", () => {
  if (!confirmReplace()) return;
  vatRateInput.value = "22";
  replaceRows([
    {name: "Бумага офисная, А4", net: "350", qty: "5", unit: "упак", source: "net"},
    {name: "Кабель USB-C, 1 м", gross: "610", qty: "3", unit: "шт", source: "gross"},
    {name: "Лента упаковочная", net: "80", qty: "2.5", unit: "м", source: "net"},
  ]);
  refreshAll();
  scheduleSettingsSave();
});
$("#importExcel").addEventListener("click", () => backend?.importExcel());
$("#exportExcel").addEventListener("click", () => requestExport("exportExcel"));
$("#exportWord").addEventListener("click", () => requestExport("exportWord"));
$("#saveSettings").addEventListener("click", saveSettings);
$$(".panel--settings input, .panel--settings textarea").forEach(input => input.addEventListener("input", scheduleSettingsSave));
vatRateInput.addEventListener("input", refreshAll);
$$("[data-detail-label]").forEach((row, index) => {
  $("textarea", row).id = `detail-${index}`;
  $("label", row).htmlFor = `detail-${index}`;
});
const setNativeControls = enabled => {
  for (const id of ["importExcel", "exportExcel", "exportWord", "saveSettings"]) {
    $(`#${id}`).disabled = !enabled;
    $(`#${id}`).title = enabled ? "" : "Доступно в настольном приложении PyNDS";
  }
};
setNativeControls(false);
activateTab("data");
addRows();
refreshAll();
if (typeof qt !== "undefined" && typeof QWebChannel !== "undefined" && qt.webChannelTransport) {
  new QWebChannel(qt.webChannelTransport, channel => {
    backend = channel.objects.backend;
    backend.importDataReady.connect(importRows);
    backend.settingsReady.connect(payload => {
      try { applySettings(JSON.parse(payload)); }
      catch { setStatus("Не удалось загрузить настройки.", true); }
      loadingSettings = false;
    });
    backend.settingsSaved.connect((ok, message) => setStatus(message, !ok));
    setNativeControls(true);
    $("#modeLabel").textContent = "Настольное приложение · файлы хранятся локально";
    backend.requestSettings();
  });
} else {
  loadingSettings = false;
  $("#modeLabel").textContent = "Браузерное демо · импорт и экспорт доступны в настольном приложении";
}
