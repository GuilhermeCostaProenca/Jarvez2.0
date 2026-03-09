import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { WeaponPurposeRangedShooting } from '../../WeaponPurpose';
import { MartialWeapon } from './MartialWeapon';
import { type MartialWeaponName } from './MartialWeaponName';
export declare class HeavyCrossbow extends MartialWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: MartialWeaponName;
    static purposes: WeaponPurposeRangedShooting[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: MartialWeaponName;
    purposes: WeaponPurposeRangedShooting[];
    price: number;
}
