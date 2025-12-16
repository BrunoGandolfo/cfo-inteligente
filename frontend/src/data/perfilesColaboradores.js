export const perfilesColaboradores = {
  "kblanco@grupoconexion.uy": {
    nombre: "Karina",
    perfil: "Persona muy alegre que le gusta bailar zumba. Siempre está con una sonrisa. Genera una hermosa energía en el estudio y siempre está disponible para los demás.",
    tono: "alegre, positivo, con energía"
  },
  "naraujo@grupoconexion.uy": {
    nombre: "Nicolás",
    perfil: "Contador, ex jugador de básquetbol (ya no juega tanto, juega poco y no muy bien). Hincha de Independiente de básquetbol. Es el contador que lleva todos los números y es muy querido por las clientas.",
    tono: "amigable, con referencias a básquet o números de forma simpática"
  },
  "gferrari@grupoconexion.uy": {
    nombre: "Gerardo",
    perfil: "Abogado que parece serio pero en realidad es muy divertido. Muy responsable. Le gusta muchísimo el derecho. Aprecia frases en latín jurídico y referencias legales.",
    tono: "profesional pero con humor sutil, puede incluir frases en latín jurídico"
  }
};

export const getPerfilByEmail = (email) => {
  return perfilesColaboradores[email?.toLowerCase()] || null;
};


