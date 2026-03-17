import { WeaponPurpose, type WeaponPurposeParams } from './WeaponPurpose';
type WeaponPurposeMeleeParams = Omit<WeaponPurposeParams, 'defaultSkill'>;
export declare class WeaponPurposeMelee extends WeaponPurpose {
    constructor(params?: WeaponPurposeMeleeParams);
}
export {};
