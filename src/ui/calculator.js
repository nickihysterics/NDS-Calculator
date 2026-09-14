/* Exact decimal arithmetic. Same rounding contract as calculations.py. */
((root) => {
  const divide = (value, divisor) => (value + divisor / 2n) / divisor;
  const scaled = (raw, precision, maximum, fallback = null) => {
    const text = String(raw ?? "").replace(/\s/g, "").replace(",", ".");
    if (!text) return fallback;
    if (!/^(\d+(\.\d*)?|\.\d+)$/.test(text) || !Number.isFinite(Number(text)) || Number(text) > maximum) {
      throw new Error(`Введите число от 0 до ${maximum.toLocaleString("ru-RU")}.`);
    }
    const [whole, fraction = ""] = text.split(".");
    const digits = fraction.padEnd(precision + 1, "0");
    const value = BigInt(whole || "0") * (10n ** BigInt(precision)) + BigInt(digits.slice(0, precision) || "0");
    return value + (Number(digits[precision]) >= 5 ? 1n : 0n);
  };
  const decimal = (value, precision = 2) => {
    const text = value.toString().padStart(precision + 1, "0");
    return `${text.slice(0, -precision)}.${text.slice(-precision)}`;
  };
  const format = (value) => {
    const [whole, fraction] = decimal(value).split(".");
    return `${BigInt(whole).toLocaleString("ru-RU")},${fraction}`;
  };
  const calculate = (raw, rateValue) => {
    const rate = scaled(rateValue, 2, 100, 2200n);
    const qty = scaled(raw.qty, 3, 1000000, 1000n);
    if (qty === 0n) throw new Error("Количество должно быть не меньше 0,001.");
    const source = raw.source === "net" ? "net" : "gross";
    const price = scaled(raw[source], 2, 1000000000);
    if (price === null) throw new Error("Укажите цену с НДС или без НДС.");
    const net = source === "net" ? price : divide(price * 10000n, 10000n + rate);
    const gross = source === "gross" ? price : divide(price * (10000n + rate), 10000n);
    if (gross > 100000000000n) throw new Error("Цена с НДС превышает 1 000 000 000.");
    const sumNet = divide(net * qty, 1000n);
    const sumGross = divide(gross * qty, 1000n);
    return {net, gross, vat: gross - net, qty, sumNet, sumGross, sumVat: sumGross - sumNet};
  };
  const api = {scaled, decimal, format, calculate};
  if (typeof module !== "undefined") module.exports = api;
  root.PyNDSCalculator = api;
})(globalThis);
