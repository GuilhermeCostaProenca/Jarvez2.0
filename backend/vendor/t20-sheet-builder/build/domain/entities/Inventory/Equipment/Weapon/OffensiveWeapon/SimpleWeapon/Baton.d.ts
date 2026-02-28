import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { WeaponPurposeMelee } from '../../WeaponPurpose';
import { SimpleWeapon } from './SimpleWeapon';
import { type SimpleWeaponName } from './SimpleWeaponName';
export declare class Baton extends SimpleWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: SimpleWeaponName;
    static purposes: WeaponPurposeMelee[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: SimpleWeaponName;
    purposes: WeaponPurposeMelee[];
    price: number;
}
