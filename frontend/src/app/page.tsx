import styles from "./page.module.css";
import { BackendStatus } from "./backend-status";

export default function Home() {
  return (
    <main className={styles.main}>
      <h1>AutoGuardian</h1>
      <p>Your personal AI vehicle health assistant.</p>
      <BackendStatus />
    </main>
  );
}
