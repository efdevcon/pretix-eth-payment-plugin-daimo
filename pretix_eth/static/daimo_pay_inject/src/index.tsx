import { useEffect } from "react";
import * as React from "react";
import { createRoot } from "react-dom/client";
import { Providers } from "./Providers";
import { useDaimoPayStatus, usePayContext } from "@daimo/pay";

inject();

function inject() {
  console.log("Pretix Daimo Pay plugin injecting...");

  const root = document.querySelector("#daimo-pay-inject-root");
  const newRoot = createRoot(root as HTMLElement);
  newRoot.render(<PayInject />);
}

function PayInject() {
  return <Providers children={<Injector />} />;
}

function Injector() {
  const context = usePayContext();

  useEffect(() => {
    // Set payment ID immediately
    const payId = window["payment_id"] as string;
    context.paymentState.setPayId(payId);

    // On form submit, show the payment modal
    const placeOrderButton = document.querySelector(
      'button.btn-primary[type="submit"]'
    ) as HTMLButtonElement;
    console.log(`Enabling place order button`, placeOrderButton);
    console.log(`Setting data-pay-id to ${payId}`);
    placeOrderButton.dataset.payId = payId;
    placeOrderButton.disabled = false;

    const form = placeOrderButton.form;
    if (form == null) {
      console.error("Place order button is not in a form");
      return;
    }
    form.onsubmit = (e) => {
      console.log("Handling Place Order submit button");
      e.preventDefault(); // Prevent submit
      e.stopPropagation(); // Prevent Pretix "place binding order" flow
      context.showPayment({});
    };
  }, []);

  // Once payment succeeds, submit the form.
  const payStatus = useDaimoPayStatus();
  useEffect(() => {
    if (payStatus?.status === "payment_completed") {
      console.log("Payment completed, submitting form");
      window.setTimeout(() => {
        document.forms[0].submit();
      }, 1000);
    }
  }, [payStatus?.status]);

  return null;
}
