export const formatNumber = (num: number, decimals = 2) => {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

export const formatSize = (bytes: number) => {
  const mb = bytes / (1024 * 1024);
  return `${formatNumber(mb)} MB`;
};
