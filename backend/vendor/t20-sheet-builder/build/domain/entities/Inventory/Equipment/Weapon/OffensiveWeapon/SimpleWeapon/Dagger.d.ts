import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { WeaponPurposeMelee, WeaponPurposeRangedThrowing } from '../../WeaponPurpose';
import { SimpleWeapon } from './SimpleWeapon';
import { type SimpleWeaponName } from './SimpleWeaponName';
export declare class Dagger extends SimpleWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: SimpleWeaponName;
    static purposes: (WeaponPurposeMelee | WeaponPurposeRangedThrowing)[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: SimpleWeaponName;
    purposes: (WeaponPurposeMelee | WeaponPurposeRangedThrowing)[];
    price: number;
}
