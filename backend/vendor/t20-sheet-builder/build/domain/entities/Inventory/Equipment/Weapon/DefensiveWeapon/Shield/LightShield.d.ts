import { EquipmentName } from '../../../EquipmentName';
import { Shield } from './Shield';
export declare class LightShield extends Shield {
    defenseBonus: number;
    armorPenalty: number;
    slots: number;
    name: EquipmentName;
    price: number;
}
