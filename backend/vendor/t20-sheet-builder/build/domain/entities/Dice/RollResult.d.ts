export type RollResultParams = {
    total: number;
    rolls: number[];
    discartedRolls: number[];
};
export declare class RollResult {
    total: number;
    readonly rolls: number[];
    readonly discartedRolls: number[];
    constructor(params: RollResultParams);
    append(rollResult: RollResult): void;
}
