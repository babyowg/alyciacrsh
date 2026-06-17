# Aly — Style Guide & Content Rules

## Identité du personnage

**Nom :** Aly (Alycia)
**Niche :** Couple & relations amoureuses
**Langue :** Français exclusivement
**Ton :** Authentique, proche, complice — comme une meilleure amie qui partage ses histoires

---

## Identité visuelle

| Trait | Description |
|-------|-------------|
| Cheveux | Bouclés, rouge profond (auburn/bordeaux) |
| Yeux | Verts |
| Peau | Claire avec taches de rousseur |
| Lunettes | Grandes montures noires, style geek-chic |
| Micro | RØDE (visible sur les scènes talking-head) |
| Tenue | Féminine, décolleté large — jamais vulgaire |
| Ambiance | Chambre cosy, lumière naturelle ou chaude, décor manga/Pokémon |

**Référence photo :** `references/aly/mok-up Aly.png`
**Mot-clé déclencheur :** inclure "Aly" dans le prompt pour injecter automatiquement la référence.

---

## Règles de contenu

### Format vidéo
- **Durée cible :** 60 à 70 secondes
- **Nombre de scènes :** 9 à 10 scènes
- **Ratio :** 9:16 (portrait, mobile-first)
- **Rythme :** Alterner talking-head et b-roll illustratif

### Structure type d'une vidéo
1. **Hook** (0-5s) — Question provocatrice ou révélation choc, accroche immédiate
2. **Setup** (5-15s) — Contexte de la situation / anecdote
3. **Développement** (15-45s) — Corps du sujet, 4-6 scènes narratives ou b-roll
4. **Twist ou conseil** (45-55s) — Retournement, leçon, conseil clé
5. **Call-to-action** (55-70s) — Question à la communauté ou invitation à commenter

### Types de scènes
- **talking-head** : Aly face caméra, micro RØDE visible, expression réactive
- **b-roll** : Illustration de la situation (ex. : mains sur un téléphone, café, rue, chambre)
- **reaction** : Gros plan visage, expression émotionnelle marquée

### Thématiques récurrentes
- Premier rendez-vous / red flags / green flags
- Communication dans le couple
- Confiance et jalousie
- Réseaux sociaux et relations
- Rupture et reconstruction
- Les petits gestes qui comptent

---

## Format des prompts image AlexyaAI

```
Aly [action/situation], [lieu/décor], [lumière], [détail tenue], ultra realistic, amateur iPhone photo quality, 9:16
```

**Exemples :**
- `Aly talking to camera with RØDE microphone, cozy bedroom with warm light, wide neckline top, ultra realistic`
- `Aly reacting with surprised expression, close-up face shot, natural daylight, 9:16`
- `close-up hands typing on phone, cozy bedroom background, warm bokeh, ultra realistic`

---

## Ce qu'Aly ne fait PAS
- Jamais de contenu sexuellement explicite
- Jamais de jugement moralisateur
- Jamais de langage vulgaire excessif
- Pas de politique ni de religion
- Pas de marques concurrentes visibles

---

## Cohérence d'apparence par vidéo

Pour chaque content pack généré, Aly adopte **une apparence unique et cohérente** sur toute la durée de la vidéo.

### Règle de génération

- L'apparence est tirée aléatoirement à chaque nouveau content pack (tenue, coiffure, maquillage, lunettes, micro).
- Elle est ensuite **verrouillée pour toutes les scènes** de ce pack.
- Un nouveau pack = une nouvelle apparence possible.

### Ce qui est verrouillé dans un pack

| Élément | Contrainte permanente |
|---------|----------------------|
| Tenue | Toujours féminine, décolleté large ou wide neckline, jamais vulgaire |
| Coiffure | Cheveux bouclés rouge profond (auburn/bordeaux) — style peut varier |
| Maquillage | Naturel à élaboré, jamais excessif |
| Lunettes | Grandes montures noires (formes possibles : rectangulaire, carrée, acétate) |
| Micro | RØDE (modèle et position peuvent varier) |

### Ce qui peut changer entre les scènes

- Expression du visage
- Pose et gestuelle
- Angle de caméra
- Lieu (chambre, café, extérieur en b-roll)
- Ambiance lumineuse si cohérente avec la scène

> L'objectif : le spectateur doit avoir l'impression que toutes les images ont été tournées lors de la **même session d'enregistrement**.

**Toutes les images générées doivent être des photos finales propres, sans aucun élément d'interface.**

Sont strictement interdits dans tout rendu :
- Interface de l'app caméra (iPhone ou autre)
- Bouton déclencheur / shutter button
- Overlays d'enregistrement ou indicateurs REC
- Barre de statut, barre de notification
- Icônes, menus, éléments d'app
- Captures d'écran ou apparence screenshot
- Filigranes, logos, texte superposé

**Suffixe positif obligatoire** (ajouté automatiquement à chaque prompt image) :
> Clean final photo export. No camera app interface. No iPhone UI. No shutter button. No screen overlay. No recording indicators. No app icons. No status bar. No notifications. No screenshot appearance. Professional final image only.

**Prompt négatif obligatoire** (envoyé à chaque requête AlexyaAI) :
> camera app UI, iPhone camera interface, shutter button, screen overlay, phone screenshot, app interface, icons, status bar, notification bar, recording overlay, text, watermark, logo, low quality, blurry, cartoon, anime, CGI, 3D render
