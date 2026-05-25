import { useState } from 'react';
import {
  StyleSheet, Text, View, TextInput,
  TouchableOpacity, ScrollView, ActivityIndicator
} from 'react-native';

const API_URL = 'https://sportiq-production.up.railway.app';
const STARS = (n) => '⭐'.repeat(n) + '☆'.repeat(5 - n);

const SPORTS = [
  { key: 'football', label: '⚽ Football' },
  { key: 'basketball', label: '🏀 Basketball' },
  { key: 'tennis', label: '🎾 Tennis' },
];

export default function App() {
  const [sport, setSport] = useState('football');
  const [home, setHome] = useState('Real Madrid');
  const [away, setAway] = useState('Atlético Madrid');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  const onSportChange = (key) => {
    setSport(key);
    setPrediction(null);
    setError(null);
    if (key === 'basketball') {
      setHome('Los Angeles Lakers');
      setAway('Boston Celtics');
    } else if (key === 'tennis') {
      setHome('Novak Djokovic');
      setAway('Carlos Alcaraz');
    } else {
      setHome('Real Madrid');
      setAway('Atlético Madrid');
    }
  };

  const predict = async () => {
    setLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const res = await fetch(
        `${API_URL}/predict?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&sport=${sport}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erreur API');
      setPrediction(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logo}>🏆 Sportiq</Text>
        <Text style={styles.subtitle}>Prédictions IA</Text>
      </View>

      {/* Sélecteur de sport */}
      <View style={styles.sportSelector}>
        {SPORTS.map(s => (
          <TouchableOpacity
            key={s.key}
            style={[styles.sportBtn, sport === s.key && styles.sportBtnActive]}
            onPress={() => onSportChange(s.key)}
          >
            <Text style={[styles.sportBtnText, sport === s.key && styles.sportBtnTextActive]}>
              {s.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Input */}
      <View style={styles.card}>
        <TextInput
          style={styles.input}
          value={home}
          onChangeText={setHome}
          placeholder={sport === 'tennis' ? 'Joueur 1' : 'Équipe domicile'}
          placeholderTextColor="#666"
        />
        <Text style={styles.vs}>VS</Text>
        <TextInput
          style={styles.input}
          value={away}
          onChangeText={setAway}
          placeholder={sport === 'tennis' ? 'Joueur 2' : 'Équipe extérieur'}
          placeholderTextColor="#666"
        />
        <TouchableOpacity style={styles.button} onPress={predict} disabled={loading}>
          <Text style={styles.buttonText}>
            {loading ? 'Analyse en cours...' : '🔍 Analyser'}
          </Text>
        </TouchableOpacity>
      </View>

      {loading && <ActivityIndicator size="large" color="#00ff88" style={{ margin: 20 }} />}

      {error && (
        <View style={styles.errorCard}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      {prediction && (
        <View>
          <View style={styles.matchCard}>
            <Text style={styles.matchTitle}>{prediction.match}</Text>
            <Text style={styles.analyse}>{prediction.analyse}</Text>
          </View>

          <Text style={styles.sectionTitle}>Prédictions</Text>
          {Object.entries(prediction.predictions || {}).map(([key, val]) => (
            <View key={key} style={styles.predCard}>
              <View style={styles.predHeader}>
                <Text style={styles.predName}>{key.toUpperCase()}</Text>
                <Text style={styles.stars}>{STARS(val.stars)}</Text>
              </View>
              <Text style={styles.predResult}>→ {val.result}</Text>
              <Text style={styles.predConfidence}>Confiance : {val.confidence_pct}%</Text>
              <Text style={styles.predReason}>{val.reasoning}</Text>
            </View>
          ))}

          {prediction.paris_impossibles?.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>⚠️ Données insuffisantes</Text>
              {prediction.paris_impossibles.map((p, i) => (
                <View key={i} style={styles.impossibleCard}>
                  <Text style={styles.impossibleText}>
                    {p.paris.join(', ')} — {p.raison}
                  </Text>
                </View>
              ))}
            </>
          )}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a1a', padding: 16 },
  header: { alignItems: 'center', paddingVertical: 30 },
  logo: { fontSize: 32, fontWeight: 'bold', color: '#00ff88' },
  subtitle: { fontSize: 14, color: '#666', marginTop: 4 },
  sportSelector: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  sportBtn: { flex: 1, padding: 10, borderRadius: 8, backgroundColor: '#1a1a2e', marginHorizontal: 4, alignItems: 'center' },
  sportBtnActive: { backgroundColor: '#00ff88' },
  sportBtnText: { color: '#aaa', fontSize: 12, fontWeight: 'bold' },
  sportBtnTextActive: { color: '#0a0a1a' },
  card: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 16, marginBottom: 16 },
  input: { backgroundColor: '#0a0a1a', color: '#fff', borderRadius: 8, padding: 12, marginBottom: 8, fontSize: 16, borderWidth: 1, borderColor: '#333' },
  vs: { textAlign: 'center', color: '#666', fontSize: 16, marginVertical: 4 },
  button: { backgroundColor: '#00ff88', borderRadius: 8, padding: 14, alignItems: 'center', marginTop: 8 },
  buttonText: { color: '#0a0a1a', fontWeight: 'bold', fontSize: 16 },
  errorCard: { backgroundColor: '#2a1a1a', borderRadius: 12, padding: 16, marginBottom: 12 },
  errorText: { color: '#ff4444' },
  matchCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 16, marginBottom: 12 },
  matchTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff', textAlign: 'center' },
  analyse: { color: '#aaa', marginTop: 8, textAlign: 'center', lineHeight: 20 },
  sectionTitle: { color: '#00ff88', fontSize: 16, fontWeight: 'bold', marginVertical: 12 },
  predCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 16, marginBottom: 8 },
  predHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  predName: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  stars: { fontSize: 14 },
  predResult: { color: '#00ff88', fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  predConfidence: { color: '#aaa', fontSize: 13, marginBottom: 4 },
  predReason: { color: '#666', fontSize: 12 },
  impossibleCard: { backgroundColor: '#1a1a1a', borderRadius: 8, padding: 12, marginBottom: 8 },
  impossibleText: { color: '#666', fontSize: 12 },
});