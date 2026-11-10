-- HU-05: fecha de fin de la suspensión de 7 días
ALTER TABLE "User" ADD COLUMN "penaltyUntil" TIMESTAMP(3);

-- HU-07: foto (URL) y código QR (cadena) del equipo
ALTER TABLE "Equipment" ADD COLUMN "photoUrl" TEXT NOT NULL DEFAULT '';
ALTER TABLE "Equipment" ADD COLUMN "qrCode" TEXT NOT NULL DEFAULT '';
