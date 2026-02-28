import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { FireArmWeapon } from './FireArmWeapon';
import { type FireArmWeaponName } from './FireArmWeaponName';
export declare class Musket extends FireArmWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: FireArmWeaponName;
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: FireArmWeaponName;
    price: number;
}
