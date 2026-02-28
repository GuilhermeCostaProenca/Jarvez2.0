import { type Devotion, type SerializedDevotion } from '../Devotion/Devotion';
import { type GrantedPowerName, type GrantedPower } from '../Power';
import { type TransactionInterface } from './TransactionInterface';
export type SerializedSheetDevotion = {
    devotion?: SerializedDevotion;
    grantedPowerCount: number;
};
export declare class SheetDevotion {
    private devotion;
    private grantedPowerCount;
    isDevout(): boolean;
    becomeDevout(devotion: Devotion, transaction: TransactionInterface): void;
    getGrantedPowerCount(): number;
    changeGrantedPowerCount(count: number): void;
    getDeity(): import("..").Deity | undefined;
    addGrantedPower(power: GrantedPower): void;
    removeGrantedPower(powerName: GrantedPowerName): void;
    serialize(): {
        devotion: SerializedDevotion | undefined;
        grantedPowerCount: number;
    };
}
