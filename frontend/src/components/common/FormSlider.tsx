interface FormSliderProps {
  label: string;
  name: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  disabled?: boolean;
  helperText?: string;
  showValue?: boolean;
  valueFormatter?: (value: number) => string;
}

export const FormSlider = ({
  label,
  name,
  value,
  onChange,
  min,
  max,
  step = 1,
  disabled = false,
  helperText,
  showValue = true,
  valueFormatter = (v) => v.toString(),
}: FormSliderProps) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label htmlFor={name} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        {showValue && (
          <span className="text-sm font-semibold text-gray-900">
            {valueFormatter(value)}
          </span>
        )}
      </div>
      <input
        type="range"
        id={name}
        name={name}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 accent-blue-600"
      />
      <div className="flex justify-between text-xs text-gray-500">
        <span>{min}</span>
        <span>{max}</span>
      </div>
      {helperText && <p className="text-sm text-gray-500">{helperText}</p>}
    </div>
  );
};
