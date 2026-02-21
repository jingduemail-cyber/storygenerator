import json
import base64
import streamlit as st
import streamlit.components.v1 as components


def save_intake_to_localstorage(key: str, intake: dict) -> None:
    payload = json.dumps(intake, ensure_ascii=False)
    components.html(
        f"""
        <script>
          localStorage.setItem({json.dumps(key)}, {json.dumps(payload)});
        </script>
        """,
        height=0,
    )


def _b64url_encode_utf8(s: str) -> str:
    b = s.encode("utf-8")
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64url_decode_utf8(s: str) -> str:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii")).decode("utf-8")


def hydrate_intake_from_localstorage_via_queryparam(local_key: str, qp_name: str = "intake") -> dict | None:
    """
    1) If intake exists in session_state -> return it.
    2) Else if query param `?intake=` exists -> decode -> set session_state -> return it.
    3) Else inject JS that reads localStorage and redirects to same page with `?intake=<b64url(JSON)>`.
       Then stop the script so the redirect can happen.
    """

    # 1) Session already has it
    intake = st.session_state.get("intake")
    if intake:
        return intake

    # 2) Query param present?
    qp = st.query_params
    token = qp.get(qp_name)
    if token:
        try:
            raw = _b64url_decode_utf8(token)
            intake = json.loads(raw)
            st.session_state.intake = intake

            # Optional: clean URL after hydrate
            try:
                st.query_params.pop(qp_name, None)
            except Exception:
                pass

            return intake
        except Exception:
            return None

    # 3) No session + no qp -> inject JS to read localStorage and redirect with qp
    components.html(
        f"""
        <script>
          (function() {{
            const key = {json.dumps(local_key)};
            const v = localStorage.getItem(key);
            if (!v) return;

            // base64url encode UTF-8 JSON
            function b64urlEncode(str) {{
              const utf8 = new TextEncoder().encode(str);
              let bin = '';
              utf8.forEach(b => bin += String.fromCharCode(b));
              const b64 = btoa(bin).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/,'');
              return b64;
            }}

            const encoded = b64urlEncode(v);
            const url = new URL(window.location.href);
            if (!url.searchParams.get({json.dumps(qp_name)})) {{
              url.searchParams.set({json.dumps(qp_name)}, encoded);
              window.location.replace(url.toString());
            }}
          }})();
        </script>
        """,
        height=0,
    )

    # Stop so Streamlit doesn't render the "No intake found" message before redirect
    st.stop()