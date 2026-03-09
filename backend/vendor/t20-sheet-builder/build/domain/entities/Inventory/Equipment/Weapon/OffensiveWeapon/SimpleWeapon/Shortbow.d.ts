import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { WeaponPurposeRangedShooting } from '../../WeaponPurpose';
import { SimpleWeapon } from './SimpleWeapon';
import { type SimpleWeaponName } from './SimpleWeaponName';
export declare class Shortbow extends SimpleWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: SimpleWeaponName;
    static purposes: WeaponPurposeRangedShooting[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: SimpleWeaponName;
    purposes: WeaponPurposeRangedShooting[];
    price: number;
}
