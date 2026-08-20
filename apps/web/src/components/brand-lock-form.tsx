"use client";

import Image from "next/image";
import { useState } from "react";

import { BRAND_LOCK_FORM_SPEC } from "../brand-lock/brand-lock-form-spec";
import type { BrandLock, BrandLockConfirmed } from "../generated/contracts";

import styles from "./brand-lock-form.module.css";

export type ConfirmBrandLock = (brandLock: BrandLock) => Promise<BrandLockConfirmed>;

interface LayoutPreview {
  headline: string;
  body: string;
  cta_label: string;
}

interface BrandLockFormProps {
  initialBrandLock: BrandLock;
  directionLabel: string;
  logoAssetPath: string;
  productUiAssetPath: string;
  layoutPreview: LayoutPreview;
  confirmBrandLock: ConfirmBrandLock;
}

function LockedValues({ brandLock }: { brandLock: BrandLock }) {
  return (
    <>
      <div><dt>Product name</dt><dd>{brandLock.product_name}</dd></div>
      <div><dt>Verified product facts</dt><dd><ul>{brandLock.verified_product_facts.map((value) => <li key={value}>{value}</li>)}</ul></dd></div>
      <div><dt>Product UI assets</dt><dd><ul>{brandLock.product_ui_asset_ids.map((value) => <li key={value}><code>{value}</code></li>)}</ul></dd></div>
      <div><dt>CTA action meaning</dt><dd>{brandLock.cta_action_meaning}</dd></div>
    </>
  );
}

export function BrandLockForm({
  initialBrandLock,
  directionLabel,
  logoAssetPath,
  productUiAssetPath,
  layoutPreview,
  confirmBrandLock,
}: BrandLockFormProps) {
  const [benefits, setBenefits] = useState<string[]>([...initialBrandLock.benefit_order]);
  const [localizable, setLocalizable] = useState<string[]>([
    ...initialBrandLock.localizable_fields,
  ]);
  const [state, setState] = useState<"ready" | "pending" | "confirmed" | "error">(
    "ready",
  );
  const immutable = state === "confirmed";
  const disabled = state === "pending" || immutable;

  function moveBenefit(index: number, offset: number) {
    const target = index + offset;
    if (target < 0 || target >= benefits.length || disabled) return;
    const reordered = [...benefits];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    setBenefits(reordered);
  }

  function toggleLocalizable(field: string) {
    if (disabled) return;
    setLocalizable((current) =>
      current.includes(field)
        ? current.filter((value) => value !== field)
        : initialBrandLock.localizable_fields.filter(
            (value) => current.includes(value) || value === field,
          ),
    );
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (localizable.length === 0 || disabled) return;
    setState("pending");
    try {
      await confirmBrandLock({
        ...initialBrandLock,
        benefit_order: benefits as BrandLock["benefit_order"],
        localizable_fields: localizable as BrandLock["localizable_fields"],
      });
      setState("confirmed");
    } catch {
      setState("error");
    }
  }

  return (
    <section className={styles.formPanel} aria-labelledby="confirm-brand-lock-heading">
      <div className={styles.headingRow}>
        <div><p className={styles.eyebrow}>Day 10 · confirmation</p><h2 id="confirm-brand-lock-heading">Confirm Brand Lock</h2></div>
        <code>{immutable ? "in_progress" : "awaiting_brand_lock"}</code>
      </div>
      <p>Locked fields are read-only. Only benefit priority and the approved localizable subset can change before confirmation.</p>
      <p>Cultural hypotheses remain pending human review.</p>

      <form onSubmit={submit}>
        <dl className={styles.fields}>
          <div><dt>Logo asset</dt><dd><code>{initialBrandLock.logo_asset_id}</code><Image src={logoAssetPath} alt={`${directionLabel} logo asset preview`} width={320} height={120} /></dd></div>
          <LockedValues brandLock={initialBrandLock} />
          <div><dt>Layout template</dt><dd><code>{initialBrandLock.layout_template_asset_id}</code><figure aria-label={`${directionLabel} layout template preview`}><strong>{layoutPreview.headline}</strong><p>{layoutPreview.body}</p><span>{layoutPreview.cta_label}</span></figure></dd></div>
        </dl>

        <fieldset disabled={disabled} className={styles.mutableField}>
          <legend>Benefit order</legend>
          <p>{BRAND_LOCK_FORM_SPEC.find((field) => field.key === "benefit_order")?.help}</p>
          <ol>{benefits.map((benefit, index) => <li key={benefit}><span>{benefit}</span><button type="button" onClick={() => moveBenefit(index, -1)} disabled={disabled || index === 0} aria-label={`Move ${benefit} up`}>↑</button><button type="button" onClick={() => moveBenefit(index, 1)} disabled={disabled || index === benefits.length - 1} aria-label={`Move ${benefit} down`}>↓</button></li>)}</ol>
        </fieldset>

        <fieldset disabled={disabled} className={styles.mutableField}>
          <legend>Localizable fields</legend>
          <p>{BRAND_LOCK_FORM_SPEC.find((field) => field.key === "localizable_fields")?.help}</p>
          {initialBrandLock.localizable_fields.map((field) => <label key={field}><input type="checkbox" checked={localizable.includes(field)} onChange={() => toggleLocalizable(field)} /> <code>{field}</code></label>)}
        </fieldset>

        <button type="submit" disabled={disabled || localizable.length === 0}>
          {state === "pending" ? "Confirming…" : "Confirm Brand Lock"}
        </button>
        {state === "error" ? <p role="alert">Unable to confirm Brand Lock.</p> : null}
        {immutable ? <p role="status">Brand Lock confirmed and immutable.</p> : null}
      </form>
      <Image className={styles.productPreview} src={productUiAssetPath} alt={`${directionLabel} product UI asset preview`} width={560} height={315} />
    </section>
  );
}
