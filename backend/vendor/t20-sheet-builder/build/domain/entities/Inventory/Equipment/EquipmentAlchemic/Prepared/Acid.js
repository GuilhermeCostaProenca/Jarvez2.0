"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Acid = void 0;
const EquipmentName_1 = require("../../EquipmentName");
const EquipmentAlchemic_1 = require("../EquipmentAlchemic");
const EquipmentAlchemicCategory_1 = require("../EquipmentAlchemicCategory");
class Acid extends EquipmentAlchemic_1.EquipmentAlchemic {
    constructor() {
        super(...arguments);
        this.alchemicCategory = EquipmentAlchemicCategory_1.EquipmentAlchemicCategory.prepared;
        this.price = 10;
        this.description = 'Frasco de vidro contendo um ácido alquímico'
            + ' altamente corrosivo. Para usar o ácido, você'
            + ' gasta uma ação padrão e escolhe uma criatura em'
            + ' alcance curto. Essa criatura sofre 2d4 pontos de dano'
            + ' de ácido (Reflexos CD Des reduz à metade).';
        this.name = EquipmentName_1.EquipmentName.acid;
        this.isWieldable = true;
    }
}
exports.Acid = Acid;
