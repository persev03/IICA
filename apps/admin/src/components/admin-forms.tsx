'use client';

import type { Session } from '@supabase/supabase-js';
import type { FormEvent, InputHTMLAttributes, ReactNode } from 'react';
import { useState } from 'react';

const apiUrl =
  process.env.NEXT_PUBLIC_IICA_API_URL ||
  (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '');

type FormKind = 'brand' | 'city' | 'vehicle' | 'mobility' | 'infrastructure' | 'tax';

const formLabels: Array<[FormKind, string]> = [
  ['brand', 'Marca'],
  ['city', 'Ciudad'],
  ['vehicle', 'Vehículo'],
  ['mobility', 'Movilidad'],
  ['infrastructure', 'Infraestructura'],
  ['tax', 'Impuesto'],
];

const value = (form: FormData, key: string) => String(form.get(key) ?? '').trim();
const numberValue = (form: FormData, key: string) => Number(value(form, key));
const optionalNumberValue = (form: FormData, key: string) =>
  value(form, key) ? Number(value(form, key)) : null;
const optionalValue = (form: FormData, key: string) => value(form, key) || null;

function payloadFor(kind: FormKind, form: FormData): object {
  if (kind === 'brand') {
    return { name: value(form, 'name'), slug: value(form, 'slug') };
  }
  if (kind === 'city') {
    return {
      country_code: value(form, 'country_code'),
      code: value(form, 'code'),
      name: value(form, 'name'),
    };
  }
  if (kind === 'vehicle') {
    return {
      brand_slug: value(form, 'brand_slug'),
      model_name: value(form, 'model_name'),
      model_slug: value(form, 'model_slug'),
      body_style: value(form, 'body_style'),
      trim: value(form, 'trim'),
      model_year: numberValue(form, 'model_year'),
      powertrain: value(form, 'powertrain'),
      seats: numberValue(form, 'seats'),
      safety_score: numberValue(form, 'safety_score'),
      warranty_months: numberValue(form, 'warranty_months'),
      list_price: numberValue(form, 'list_price'),
      currency_code: value(form, 'currency_code'),
      market_as_of: value(form, 'market_as_of'),
      expected_annual_depreciation_percentage: optionalNumberValue(
        form,
        'expected_annual_depreciation_percentage',
      ),
      liquidity_score: optionalNumberValue(form, 'liquidity_score'),
      owner_satisfaction_score: optionalNumberValue(form, 'owner_satisfaction_score'),
      source_url: value(form, 'source_url'),
    };
  }
  if (kind === 'mobility') {
    return {
      city_code: value(form, 'city_code'),
      name: value(form, 'name'),
      powertrain: optionalValue(form, 'powertrain'),
      restricted_days_per_month: numberValue(form, 'restricted_days_per_month'),
      exemption: form.get('exemption') === 'on',
      effective_from: value(form, 'effective_from'),
      effective_to: optionalValue(form, 'effective_to'),
      source_url: value(form, 'source_url'),
    };
  }
  if (kind === 'infrastructure') {
    return {
      city_code: value(form, 'city_code'),
      as_of: value(form, 'as_of'),
      public_charging_points: numberValue(form, 'public_charging_points'),
      authorized_workshops: numberValue(form, 'authorized_workshops'),
      dealerships: numberValue(form, 'dealerships'),
      source_url: value(form, 'source_url'),
    };
  }
  return {
    country_code: value(form, 'country_code'),
    city_code: optionalValue(form, 'city_code'),
    name: value(form, 'name'),
    tax_kind: value(form, 'tax_kind'),
    rate_percentage: numberValue(form, 'rate_percentage'),
    effective_from: value(form, 'effective_from'),
    effective_to: optionalValue(form, 'effective_to'),
    source_url: value(form, 'source_url'),
  };
}

const endpoints: Record<FormKind, string> = {
  brand: '/v1/admin/vehicle-brands',
  city: '/v1/admin/cities',
  vehicle: '/v1/admin/vehicles',
  mobility: '/v1/admin/mobility-restrictions',
  infrastructure: '/v1/admin/infrastructure-snapshots',
  tax: '/v1/admin/tax-rules',
};

export function AdminForms({
  session,
  onComplete,
  onMessage,
}: {
  session: Session;
  onComplete: () => Promise<void>;
  onMessage: (message: string) => void;
}) {
  const [active, setActive] = useState<FormKind>('city');
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    onMessage('');
    const response = await fetch(`${apiUrl}${endpoints[active]}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payloadFor(active, new FormData(event.currentTarget))),
    });
    setSaving(false);
    if (!response.ok) {
      const payload = (await response.json()) as { detail?: string };
      onMessage(payload.detail ?? 'No fue posible guardar el registro.');
      return;
    }
    event.currentTarget.reset();
    onMessage('Registro guardado correctamente.');
    await onComplete();
  }

  return (
    <section className="record-editor" aria-labelledby="editor-title">
      <div className="record-editor-heading">
        <div>
          <p>Nuevo registro</p>
          <h2 id="editor-title">Carga controlada</h2>
        </div>
        <div className="form-tabs" role="tablist" aria-label="Tipo de registro">
          {formLabels.map(([kind, label]) => (
            <button
              className={active === kind ? 'active' : ''}
              key={kind}
              type="button"
              onClick={() => setActive(kind)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <form className="admin-form" onSubmit={submit}>
        <AdminFields kind={active} />
        <button type="submit" disabled={saving}>
          {saving ? 'Guardando…' : 'Guardar registro'}
        </button>
      </form>
    </section>
  );
}

function AdminFields({ kind }: { kind: FormKind }) {
  if (kind === 'brand') {
    return (
      <>
        <Field label="Nombre" name="name" maxLength={120} />
        <Field label="Slug" name="slug" pattern="[a-z0-9-]+" />
      </>
    );
  }
  if (kind === 'city') {
    return (
      <>
        <Field label="País" name="country_code" defaultValue="CO" maxLength={2} />
        <Field label="Código de ciudad" name="code" pattern="[a-z0-9-]+" />
        <Field label="Nombre" name="name" maxLength={150} />
      </>
    );
  }
  if (kind === 'vehicle') {
    return (
      <>
        <Field label="Slug de marca" name="brand_slug" pattern="[a-z0-9-]+" />
        <Field label="Modelo" name="model_name" />
        <Field label="Slug del modelo" name="model_slug" pattern="[a-z0-9-]+" />
        <Field label="Carrocería" name="body_style" placeholder="SUV, sedán…" />
        <Field label="Versión" name="trim" />
        <Field
          label="Año modelo"
          name="model_year"
          type="number"
          min="1886"
          max="2100"
        />
        <SelectField label="Motorización" name="powertrain">
          <option value="gasoline">Gasolina</option>
          <option value="diesel">Diésel</option>
          <option value="hybrid">Híbrido</option>
          <option value="plug_in_hybrid">Híbrido enchufable</option>
          <option value="electric">Eléctrico</option>
        </SelectField>
        <Field label="Asientos" name="seats" type="number" min="1" max="100" />
        <Field
          label="Seguridad (0–100)"
          name="safety_score"
          type="number"
          min="0"
          max="100"
          step="0.01"
        />
        <Field
          label="Garantía (meses)"
          name="warranty_months"
          type="number"
          min="0"
          max="240"
        />
        <Field
          label="Precio de lista"
          name="list_price"
          type="number"
          min="1"
          step="0.01"
        />
        <Field label="Moneda" name="currency_code" defaultValue="COP" maxLength={3} />
        <Field label="Fecha del mercado" name="market_as_of" type="date" />
        <Field
          label="Depreciación anual % (opcional)"
          name="expected_annual_depreciation_percentage"
          type="number"
          min="0"
          max="100"
          step="0.01"
          required={false}
        />
        <Field
          label="Liquidez (0–100, opcional)"
          name="liquidity_score"
          type="number"
          min="0"
          max="100"
          step="0.01"
          required={false}
        />
        <Field
          label="Satisfacción (0–100, opcional)"
          name="owner_satisfaction_score"
          type="number"
          min="0"
          max="100"
          step="0.01"
          required={false}
        />
        <Field label="Fuente oficial" name="source_url" type="url" wide />
      </>
    );
  }
  if (kind === 'mobility') {
    return (
      <>
        <Field label="Código de ciudad" name="city_code" />
        <Field label="Nombre de la regla" name="name" />
        <Field label="Motorización (opcional)" name="powertrain" />
        <Field
          label="Días restringidos/mes"
          name="restricted_days_per_month"
          type="number"
          min="0"
          max="31"
        />
        <Field label="Vigente desde" name="effective_from" type="date" />
        <Field
          label="Vigente hasta (opcional)"
          name="effective_to"
          type="date"
          required={false}
        />
        <label className="checkbox-field">
          <input name="exemption" type="checkbox" /> Exención aplicable
        </label>
        <Field label="Fuente oficial" name="source_url" type="url" wide />
      </>
    );
  }
  if (kind === 'infrastructure') {
    return (
      <>
        <Field label="Código de ciudad" name="city_code" />
        <Field label="Fecha de corte" name="as_of" type="date" />
        <Field
          label="Puntos de carga públicos"
          name="public_charging_points"
          type="number"
          min="0"
        />
        <Field
          label="Talleres autorizados"
          name="authorized_workshops"
          type="number"
          min="0"
        />
        <Field label="Concesionarios" name="dealerships" type="number" min="0" />
        <Field label="Fuente oficial" name="source_url" type="url" wide />
      </>
    );
  }
  return (
    <>
      <Field label="País" name="country_code" defaultValue="CO" maxLength={2} />
      <Field label="Ciudad (opcional)" name="city_code" required={false} />
      <Field label="Nombre de la regla" name="name" />
      <Field label="Tipo de impuesto" name="tax_kind" />
      <Field
        label="Tasa %"
        name="rate_percentage"
        type="number"
        min="0"
        max="100"
        step="0.0001"
      />
      <Field label="Vigente desde" name="effective_from" type="date" />
      <Field
        label="Vigente hasta (opcional)"
        name="effective_to"
        type="date"
        required={false}
      />
      <Field label="Fuente oficial" name="source_url" type="url" wide />
    </>
  );
}

function Field({
  label,
  wide = false,
  required = true,
  ...props
}: {
  label: string;
  wide?: boolean;
  required?: boolean;
} & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={wide ? 'wide-field' : undefined}>
      {label}
      <input {...props} required={required} />
    </label>
  );
}

function SelectField({
  label,
  name,
  children,
}: {
  label: string;
  name: string;
  children: ReactNode;
}) {
  return (
    <label>
      {label}
      <select name={name} required>
        {children}
      </select>
    </label>
  );
}
