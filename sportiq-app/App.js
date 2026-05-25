import { useState, useEffect } from 'react';
import {
  StyleSheet, Text, View, ScrollView,
  TouchableOpacity, ActivityIndicator, RefreshControl
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
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    loadMatches();
  }, [sport]);

  const loadMatches = async () => {
    setLoading(true);
    setSelectedMatch(null);
    setPrediction(null);
    try {
      const res = await fetch(`${API_URL}/today/${sport}`);
      const data = await res.json();
      setMatches(data.matches || []);
    } catch (e) {
      setMatches([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMatches();
    setRefreshing(false);
  };

  const analyzeMatch = async (match) => {
    setSelectedMatch(match);
    setPrediction(null);
    setPredicting(true);

    try {
      const res = await fetch(
        `${API_URL}/predict?home=${encodeURIComponent(match.team_home)}&away=${encodeURIComponent(match.team_away)}&sport=${sport}`
      );
      const data = await res.json();
      setPrediction(data);
    } catch (e) {
      setPrediction({ error: e.message });
    } finally {
      setPredicting(false);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#00ff88" />}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.logo}>🏆 Sportiq</Text>
        <Text style={styles.subtitle}>Matchs du jour</Text>
      </View>

      {/* Sélecteur sport */}
      <View style={styles.sportSelector}>
        {SPORTS.map(s => (
          <TouchableOpacity
            key={s.key}
            style={[styles.sportBtn, sport === s.key && styles.sportBtnActive]}
            onPress={() => setSport(s.key)}
          >
            <Text style={[styles.sportBtnText, sport === s.key && styles.sportBtnTextActive]}>
              {s.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Loading */}
      {loading && <ActivityIndicator size="large" color="#00ff88" style={{ margin: 30 }} />}

      {/* Liste des matchs */}
      {!loading && !selectedMatch && (
        <>
          <Text style={styles.sectionTitle}>{matches.length} match(s) à venir</Text>
          {matches.map((m, i) => (
            <TouchableOpacity key={i} style={styles.matchCard} onPress={() => analyzeMatch(m)}>
              <Text style={styles.matchLeague}>{m.league?.replace(/_/g, ' ').toUpperCase()}</Text>
              <View style={styles.matchRow}>
                <Text style={styles.teamName}>{m.team_home}</Text>
                <Text style={styles.vs}>VS</Text>
                <Text style={styles.teamName}>{m.team_away}</Text>
              </View>
              <Text style={styles.matchDate}>{formatDate(m.commence_time)}</Text>
              {m.bookmakers?.home_odds && (
                <View style={styles.oddsRow}>
                  <View style={styles.oddBox}>
                    <Text style={styles.oddLabel}>1</Text>
                    <Text style={styles.oddValue}>{m.bookmakers.home_odds}</Text>
                  </View>
                  {m.bookmakers.draw_odds && (
                    <View style={styles.oddBox}>
                      <Text style={styles.oddLabel}>N</Text>
                      <Text style={styles.oddValue}>{m.bookmakers.draw_odds}</Text>
                    </View>
                  )}
                  <View style={styles.oddBox}>
                    <Text style={styles.oddLabel}>2</Text>
                    <Text style={styles.oddValue}>{m.bookmakers.away_odds}</Text>
                  </View>
                </View>
              )}
              <Text style={styles.analyzeBtn}>🔍 Analyser ce match →</Text>
            </TouchableOpacity>
          ))}
        </>
      )}

      {/* Prédiction en cours */}
      {selectedMatch && predicting && (
        <View style={styles.predictingCard}>
          <Text style={styles.predictingTitle}>
            {selectedMatch.team_home} vs {selectedMatch.team_away}
          </Text>
          <ActivityIndicator size="large" color="#00ff88" style={{ margin: 20 }} />
          <Text style={styles.predictingText}>Analyse IA en cours...</Text>
        </View>
      )}

      {/* Résultat prédiction */}
      {selectedMatch && prediction && !predicting && (
        <View>
          <TouchableOpacity style={styles.backBtn} onPress={() => { setSelectedMatch(null); setPrediction(null); }}>
            <Text style={styles.backBtnText}>← Retour aux matchs</Text>
          </TouchableOpacity>

          <View style={styles.matchCard}>
            <Text style={styles.matchTitle}>{prediction.match}</Text>
            <Text style={styles.analyse}>{prediction.analyse}</Text>
          </View>

          {/* Cotes */}
          {selectedMatch.bookmakers?.home_odds && (
            <View style={styles.oddsCard}>
              <Text style={styles.sectionTitle}>Cotes</Text>
              <View style={styles.oddsRow}>
                <View style={styles.oddBoxLarge}>
                  <Text style={styles.oddLabel}>1 — {selectedMatch.team_home}</Text>
                  <Text style={styles.oddValueLarge}>{selectedMatch.bookmakers.home_odds}</Text>
                </View>
                {selectedMatch.bookmakers.draw_odds && (
                  <View style={styles.oddBoxLarge}>
                    <Text style={styles.oddLabel}>Nul</Text>
                    <Text style={styles.oddValueLarge}>{selectedMatch.bookmakers.draw_odds}</Text>
                  </View>
                )}
                <View style={styles.oddBoxLarge}>
                  <Text style={styles.oddLabel}>2 — {selectedMatch.team_away}</Text>
                  <Text style={styles.oddValueLarge}>{selectedMatch.bookmakers.away_odds}</Text>
                </View>
              </View>
            </View>
          )}

          {/* Prédictions */}
          <Text style={styles.sectionTitle}>Prédictions IA</Text>
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

          {/* Paris impossibles */}
          {prediction.paris_impossibles?.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>⚠️ Données insuffisantes</Text>
              {prediction.paris_impossibles.map((p, i) => (
                <View key={i} style={styles.impossibleCard}>
                  <Text style={styles.impossibleText}>{p.paris.join(', ')} — {p.raison}</Text>
                </View>
              ))}
            </>
          )}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a1a', padding: 16 },
  header: { alignItems: 'center', paddingVertical: 24 },
  logo: { fontSize: 28, fontWeight: 'bold', color: '#00ff88' },
  subtitle: { fontSize: 13, color: '#666', marginTop: 4 },
  sportSelector: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  sportBtn: { flex: 1, padding: 10, borderRadius: 8, backgroundColor: '#1a1a2e', marginHorizontal: 3, alignItems: 'center' },
  sportBtnActive: { backgroundColor: '#00ff88' },
  sportBtnText: { color: '#aaa', fontSize: 12, fontWeight: 'bold' },
  sportBtnTextActive: { color: '#0a0a1a' },
  sectionTitle: { color: '#00ff88', fontSize: 14, fontWeight: 'bold', marginVertical: 10 },
  matchCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 14, marginBottom: 10 },
  matchLeague: { color: '#555', fontSize: 10, marginBottom: 6 },
  matchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 },
  teamName: { color: '#fff', fontWeight: 'bold', fontSize: 13, flex: 1 },
  vs: { color: '#444', fontSize: 12, marginHorizontal: 8 },
  matchDate: { color: '#555', fontSize: 11, marginBottom: 8 },
  oddsRow: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 8 },
  oddBox: { backgroundColor: '#0a0a1a', borderRadius: 6, padding: 6, alignItems: 'center', minWidth: 50 },
  oddBoxLarge: { backgroundColor: '#0a0a1a', borderRadius: 8, padding: 10, alignItems: 'center', flex: 1, marginHorizontal: 4 },
  oddLabel: { color: '#666', fontSize: 10 },
  oddValue: { color: '#00ff88', fontWeight: 'bold', fontSize: 14 },
  oddValueLarge: { color: '#00ff88', fontWeight: 'bold', fontSize: 20 },
  analyzeBtn: { color: '#00ff88', fontSize: 12, marginTop: 8, textAlign: 'right' },
  predictingCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 20, alignItems: 'center', marginTop: 20 },
  predictingTitle: { color: '#fff', fontWeight: 'bold', fontSize: 16, textAlign: 'center' },
  predictingText: { color: '#666', fontSize: 13 },
  backBtn: { marginBottom: 12 },
  backBtnText: { color: '#00ff88', fontSize: 14 },
  matchTitle: { fontSize: 18, fontWeight: 'bold', color: '#fff', textAlign: 'center', marginBottom: 8 },
  analyse: { color: '#aaa', textAlign: 'center', lineHeight: 20, fontSize: 13 },
  oddsCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 14, marginBottom: 10 },
  predCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 14, marginBottom: 8 },
  predHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  predName: { color: '#fff', fontWeight: 'bold', fontSize: 13 },
  stars: { fontSize: 13 },
  predResult: { color: '#00ff88', fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
  predConfidence: { color: '#aaa', fontSize: 12, marginBottom: 4 },
  predReason: { color: '#666', fontSize: 11 },
  impossibleCard: { backgroundColor: '#111', borderRadius: 8, padding: 10, marginBottom: 6 },
  impossibleText: { color: '#555', fontSize: 11 },
});