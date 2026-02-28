import { HeavyArmor } from './HeavyArmor';
import { type HeavyArmorName } from './HeavyArmorName';
export declare class ChainMail extends HeavyArmor {
    static defenseBonus: number;
    static armorPenalty: number;
    static slots: number;
    static equipmentName: HeavyArmorName;
    static price: number;
    defenseBonus: number;
    armorPenalty: number;
    slots: number;
    name: HeavyArmorName;
    price: number;
}
