import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { WeaponPurposeMelee, WeaponPurposeRangedThrowing } from '../../WeaponPurpose';
import { MartialWeapon } from './MartialWeapon';
import { type MartialWeaponName } from './MartialWeaponName';
export declare class HandAndaHalfSword extends MartialWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: MartialWeaponName;
    static purposes: (WeaponPurposeMelee | WeaponPurposeRangedThrowing)[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: MartialWeaponName;
    purposes: (WeaponPurposeMelee | WeaponPurposeRangedThrowing)[];
    price: number;
}
