import type { ReactNode } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { session } from "./lib/session";
import Analyze from "./pages/Analyze";
import Cleanup from "./pages/Cleanup";
import Consent from "./pages/Consent";
import Draft from "./pages/Draft";
import Landing from "./pages/Landing";
import Mask from "./pages/Mask";
import Privacy from "./pages/Privacy";
import Result from "./pages/Result";
import Select from "./pages/Select";
import Upload from "./pages/Upload";
import ErrorBoundary from "./components/ErrorBoundary";
import { AppProvider } from "./state/AppState";

/** 동의 전에는 점검 화면에 들어가지 못하게 한다. */
function NeedConsent({
  children,
  next,
}: {
  children: ReactNode;
  next: "uc1" | "uc2";
}) {
  const loc = useLocation();
  if (!session.hasConsent())
    return (
      <Navigate
        to={`/consent?next=${next}`}
        replace
        state={{ from: loc.pathname }}
      />
    );
  return <>{children}</>;
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/consent" element={<Consent />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route
              path="/uc1/upload"
              element={
                <NeedConsent next="uc1">
                  <Upload />
                </NeedConsent>
              }
            />
            <Route
              path="/uc1/select"
              element={
                <NeedConsent next="uc1">
                  <Select />
                </NeedConsent>
              }
            />
            <Route
              path="/uc1/analyze"
              element={
                <NeedConsent next="uc1">
                  <Analyze />
                </NeedConsent>
              }
            />
            <Route
              path="/uc1/result"
              element={
                <NeedConsent next="uc1">
                  <Result />
                </NeedConsent>
              }
            />
            <Route
              path="/uc1/cleanup"
              element={
                <NeedConsent next="uc1">
                  <Cleanup />
                </NeedConsent>
              }
            />
            <Route
              path="/uc2"
              element={
                <NeedConsent next="uc2">
                  <Draft />
                </NeedConsent>
              }
            />
            <Route
              path="/uc2/mask"
              element={
                <NeedConsent next="uc2">
                  <Mask />
                </NeedConsent>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </ErrorBoundary>
  );
}
